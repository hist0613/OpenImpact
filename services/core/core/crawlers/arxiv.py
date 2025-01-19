import os
import pickle
from typing import Set, Dict, List, Tuple, Any, Optional
from collections import defaultdict
import time
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ArxivPaper:
    """Data class for arXiv paper information"""
    url: str
    title: str
    comment: str
    abstract: Optional[str] = None
    full_content: Optional[Dict[str, Dict[str, str]]] = None


class ArxivBaseCrawler:
    """Base crawler with common utilities"""
    def __init__(self, max_retries: int = 3, retry_delay: int = 15):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _make_request(self, url: str) -> requests.Response:
        """Make HTTP request with retry logic"""
        for trial in range(self.max_retries):
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    return response
            except requests.exceptions.ConnectionError as e:
                if trial == self.max_retries - 1:
                    raise e
                time.sleep(trial * self.retry_delay + self.retry_delay)
        raise Exception(f"Failed to get response from {url}")


class ArxivPaperCrawler(ArxivBaseCrawler):
    """Crawler for individual arXiv papers"""
    def get_paper_from_url(self, url: str) -> ArxivPaper:
        """Get paper information from arXiv URL"""
        logger.debug(f"Starting to crawl paper from URL: {url}")
        
        # Normalize URL
        url = self._normalize_url(url)
        
        # Get paper page
        paper_page = self._make_request(url)
        paper_soup = BeautifulSoup(paper_page.text, "html.parser")
        
        # Extract basic information
        title = self._extract_title(paper_soup)
        comment = self._extract_comment(paper_soup)
        
        # Create paper object
        paper = ArxivPaper(url=url, title=title, comment=comment)
        
        # Add abstract
        paper.abstract = self.get_paper_abstract(paper_soup)
        
        # Try to get full content
        html_link = self.get_html_experimental_link(paper_soup)
        if html_link != "Link not found":
            logger.debug(f"Found HTML experimental link for {title}")
            try:
                paper.full_content = self.get_paper_full_content(html_link)
            except Exception as e:
                logger.error(f"Failed to get full content: {str(e)}")
        
        return paper

    def _normalize_url(self, url: str) -> str:
        """Normalize arXiv URL format"""
        if "arxiv.org/abs/" in url:
            paper_id = url.split("arxiv.org/abs/")[-1]
            return f"https://arxiv.org/abs/{paper_id}"
        return url

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract paper title from soup"""
        try:
            title_tag = soup.find("h1", class_="title")
            return title_tag.text.strip().replace("Title:", "").strip()
        except Exception as e:
            logger.error(f"Failed to extract title: {str(e)}")
            raise

    def _extract_comment(self, soup: BeautifulSoup) -> str:
        """Extract paper comment from soup"""
        try:
            comment_tag = soup.find("td", class_="tablecell comments")
            return comment_tag.text.strip() if comment_tag else ""
        except Exception as e:
            logger.error(f"Failed to extract comment: {str(e)}")
            return ""

    def get_paper_abstract(self, soup: BeautifulSoup) -> str:
        """Get abstract from paper soup"""
        return (
            soup.find("blockquote", class_="abstract")
            .text.strip()
            .replace("Abstract: ", "")
            .replace("\n", " ")
        )

    def get_html_experimental_link(self, soup: BeautifulSoup) -> str:
        """Get HTML experimental link from paper soup"""
        html_link = soup.find("a", string="HTML (experimental)")
        return html_link["href"] if html_link else "Link not found"

    def get_paper_full_content(self, url: str) -> Dict[str, Dict[str, str]]:
        """Get full content from HTML experimental page"""
        paper_page = self._make_request(url)
        paper_soup = BeautifulSoup(paper_page.text, "html.parser")
        
        sections = paper_soup.find_all("section")
        section_dict: Dict[str, Dict[str, str]] = {}
        
        for section in sections:
            section_id = section.get("id")
            if section_id:
                title_tag = section.find("h2")
                if title_tag:
                    if title_tag.find("span"):
                        title_tag.span.decompose()
                    section_title = title_tag.text.strip()
                else:
                    section_title = "No title found"

                section_content = "\n".join(
                    [para.text.strip() for para in section.find_all("p")]
                )

                section_dict[section_id] = {
                    "title": section_title,
                    "content": section_content,
                }
                
        return section_dict


class ArxivListCrawler(ArxivBaseCrawler):
    """Crawler for arXiv paper lists"""
    def __init__(self, max_nb_crawl: int = 100, **kwargs):
        super().__init__(**kwargs)
        self.max_nb_crawl = max_nb_crawl
        self.paper_crawler = ArxivPaperCrawler(**kwargs)

    def get_paper_list(self, field: str) -> List[ArxivPaper]:
        """Get list of papers from specific field"""
        logger.info(f"Starting to crawl papers from field: {field}")
        
        # Get list page
        list_url = f"https://arxiv.org/list/{field}/pastweek?skip=0&show={self.max_nb_crawl}"
        list_page = self._make_request(list_url)
        list_soup = BeautifulSoup(list_page.text, "html.parser")

        # Find paper entries
        dt_tags = list_soup.find_all("dt")
        dd_tags = list_soup.find_all("dd")
        
        total_papers = len(dt_tags)
        logger.info(f"Found {total_papers} papers to crawl")

        papers: List[ArxivPaper] = []
        for dt_tag, dd_tag in tqdm(
            zip(dt_tags, dd_tags),
            total=total_papers,
            desc=f"Crawling {field}",
            unit="paper"
        ):
            paper_url = self._extract_paper_url(dt_tag)
            if not paper_url:
                continue
                
            try:
                paper = self.paper_crawler.get_paper_from_url(paper_url)
                papers.append(paper)
                logger.debug(f"Successfully crawled paper: {paper.title}")
            except Exception as e:
                logger.error(f"Failed to crawl paper from {paper_url}: {str(e)}")
                continue

        logger.info(f"Successfully crawled {len(papers)}/{total_papers} papers from {field}")
        return papers

    def _extract_paper_url(self, dt_tag: BeautifulSoup) -> Optional[str]:
        """Extract paper URL from dt tag"""
        try:
            url_path = dt_tag.find("a", {"title": "Abstract"})["href"]
            return "https://arxiv.org" + url_path
        except Exception as e:
            logger.error(f"Failed to extract paper URL: {str(e)}")
            return None


class ArxivCrawler:
    """Main crawler class with storage capabilities"""
    def __init__(
        self,
        base_dir: str,
        max_nb_crawl: int,
        max_retries: int = 3,
        retry_delay: int = 15
    ):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        
        # Initialize crawlers
        self.paper_crawler = ArxivPaperCrawler(
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        self.list_crawler = ArxivListCrawler(
            max_nb_crawl=max_nb_crawl,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        
        # Initialize storage paths
        self.papers_path = os.path.join(base_dir, "papers.pickle")

    def crawl_paper(self, url: str) -> ArxivPaper:
        """Crawl single paper by URL"""
        return self.paper_crawler.get_paper_from_url(url)

    def crawl_field(self, field: str) -> List[ArxivPaper]:
        """Crawl papers from specific field"""
        return self.list_crawler.get_paper_list(field)

    def _load_pickle(self, path: str, default: Any) -> Any:
        if os.path.exists(path):
            with open(path, "rb") as fp:
                return pickle.load(fp)
        return default

    def _save_pickle(self, path: str, data: Any) -> None:
        with open(path, "wb") as fp:
            pickle.dump(data, fp)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ArXiv Crawler")
    parser.add_argument("--base_dir", type=str, default="./arxiv_data", help="Base directory for storing data")
    parser.add_argument("--field", type=str, default="cs.CL", help="ArXiv field to crawl (e.g., cs.AI)")
    parser.add_argument("--url", type=str, default=None, help="Single ArXiv paper URL to crawl")
    parser.add_argument("--max_papers", type=int, default=50, help="Maximum number of papers to crawl")
    
    args = parser.parse_args()
    
    crawler = ArxivCrawler(
        base_dir=args.base_dir,
        max_nb_crawl=args.max_papers
    )
    
    if args.url:
        paper = crawler.crawl_paper(args.url)
        print(f"Crawled paper: {paper.title}")
        print(f"Abstract: {paper.abstract[:200]}...")
    
    elif args.field:
        papers = crawler.crawl_field(args.field)
        print(f"Crawled {len(papers)} papers from {args.field}")
        for paper in papers[:5]:  # Show first 5 papers
            print(f"- {paper.title}")
    
    else:
        parser.print_help()
