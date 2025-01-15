async function searchPapers() {
    const searchInput = document.getElementById('search-input');
    const resultsDiv = document.getElementById('search-results');

    try {
        // 나중에 백엔드 API가 준비되면 실제 API 호출로 변경
        const response = await fetch(`http://localhost:8000/search?query=${searchInput.value}`);
        const data = await response.json();

        // 결과 표시
        resultsDiv.innerHTML = `<p>검색 결과: ${JSON.stringify(data)}</p>`;
    } catch (error) {
        resultsDiv.innerHTML = '<p>검색 중 오류가 발생했습니다.</p>';
        console.error('Error:', error);
    }
}