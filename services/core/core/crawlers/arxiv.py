import os
import pickle
from typing import Set, Dict, List, Tuple, Any, Optional
from collections import defaultdict
import time
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from dataclasses import dataclass


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
        # Normalize URL format
        if "arxiv.org/abs/" in url:
            paper_id = url.split("arxiv.org/abs/")[-1]
            url = f"https://arxiv.org/abs/{paper_id}"
        
        # Get paper page
        paper_page = self._make_request(url)
        paper_soup = BeautifulSoup(paper_page.text, "html.parser")
        
        # Extract title
        title = paper_soup.find("h1", class_="title").text.strip().replace("Title:", "").strip()
        
        # Extract comment if exists
        comment_tag = paper_soup.find("td", class_="tablecell comments")
        comment = comment_tag.text.strip() if comment_tag else ""
        
        # Create paper object
        paper = ArxivPaper(url=url, title=title, comment=comment)
        
        # Add abstract
        paper.abstract = self.get_paper_abstract(paper_soup)
        
        # Try to get full content
        html_link = self.get_html_experimental_link(paper_soup)
        if html_link != "Link not found":
            paper.full_content = self.get_paper_full_content(html_link)
            
        return paper

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
        list_url = f"https://arxiv.org/list/{field}/pastweek?skip=0&show={self.max_nb_crawl}"
        list_page = self._make_request(list_url)
        list_soup = BeautifulSoup(list_page.text, "html.parser")

        papers: List[ArxivPaper] = []
        dt_tags = list_soup.find_all("dt")
        dd_tags = list_soup.find_all("dd")

        for dt_tag, dd_tag in zip(dt_tags, dd_tags):
            # Get paper URL
            paper_url = "https://arxiv.org" + dt_tag.find("a", {"title": "Abstract"})["href"]
            
            # Get paper details using paper crawler
            paper = self.paper_crawler.get_paper_from_url(paper_url)
            papers.append(paper)

        return papers


class ArxivCrawler:
    """Main crawler class with storage capabilities"""
    def __init__(
        self,
        base_dir: str,
        max_nb_crawl: int = 100,
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
    parser.add_argument("--field", type=str, help="ArXiv field to crawl (e.g., cs.AI)")
    parser.add_argument("--url", type=str, help="Single ArXiv paper URL to crawl")
    parser.add_argument("--max_papers", type=int, default=100, help="Maximum number of papers to crawl")
    
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
