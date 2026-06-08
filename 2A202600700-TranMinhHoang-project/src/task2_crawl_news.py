"""
Task 2 — Crawl bài báo về nghệ sĩ liên quan tới ma tuý.

Hướng dẫn:
    1. Crawl tối thiểu 5 bài báo từ các trang tin tức Việt Nam.
    2. Sử dụng Crawl4AI hoặc thư viện crawling tương tự.
    3. Lưu output vào data/landing/news/
    4. Mỗi bài lưu 1 file JSON với metadata (url, title, date_crawled, content).

Cài đặt:
    pip install crawl4ai
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


ARTICLE_URLS = [
    "https://vnexpress.net/ca-si-miu-le-bi-bat-voi-cao-buoc-to-chuc-su-dung-ma-tuy-5074769.html",
    "https://tuoitre.vn/dien-vien-huu-tin-hau-toa-sang-nay-28-4-20230428100929278.htm",
    "https://tuoitre.vn/ca-si-chi-dan-nguoi-mau-an-tay-co-tien-truc-phuong-to-chuc-su-dung-ma-tuy-ra-sao-2026040214370414.htm",
    "https://baobacninhtv.vn/truy-to-ca-si-chau-viet-cuong-ve-toi-giet-nguoi-postid294056.bbg",
    "https://vov.vn/phap-luat/cuu-dien-vien-le-hang-bi-khoi-to-se-lam-ro-nguon-goc-so-ma-tuy-thu-giu-duoc-post1016005.vov"
]


async def crawl_article(url: str) -> dict:
    """
    Crawl một bài báo và trả về dict chứa metadata + content.

    Returns:
        {
            "url": str,
            "title": str,
            "date_crawled": str (ISO format),
            "content_markdown": str
        }
    """
    import requests
    from bs4 import BeautifulSoup
    from datetime import datetime

    print(f"  -> Attempting to crawl using crawl4ai: {url}")
    try:
        from crawl4ai import AsyncWebCrawler
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            if result and result.success:
                # Extract title from metadata or html
                title = result.metadata.get("title") or ""
                if not title and result.cleaned_html:
                    soup = BeautifulSoup(result.cleaned_html, "html.parser")
                    title = soup.title.string if soup.title else ""
                
                if not title:
                    title = "Unknown Title"
                
                return {
                    "url": url,
                    "title": title.strip(),
                    "date_crawled": datetime.now().isoformat(),
                    "content_markdown": result.markdown or ""
                }
    except Exception as e:
        print(f"  -> crawl4ai failed: {e}. Falling back to requests + BeautifulSoup + markitdown.")

    # Fallback using requests + BeautifulSoup + markitdown
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        html = response.content
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract title
        title = ""
        title_tags = [
            soup.find("h1", class_="title-detail"),
            soup.find("h1", class_="article-title"),
            soup.find("h1", class_="detail-title"),
            soup.find("h1", class_="media-title"),
            soup.find("h1", class_="title"),
            soup.find("h1", class_="post-title"),
            soup.find("h1")
        ]
        for tag in title_tags:
            if tag:
                title = tag.get_text()
                break
        if not title and soup.title:
            title = soup.title.get_text()
        if not title:
            title = "Unknown Title"
            
        # Extract content
        content_markdown = ""
        try:
            from markitdown import MarkItDown
            md = MarkItDown()
            result = md.convert_response(response)
            content_markdown = result.text_content
        except Exception as md_err:
            print(f"  -> markitdown failed: {md_err}. Falling back to paragraph extraction.")
            content_div = (
                soup.find("article", class_="fck_detail") or 
                soup.find("div", class_="detail-content") or 
                soup.find("div", class_="text-content") or
                soup.find("div", id="main-detail-body") or
                soup.find("div", class_="content")
            )
            if content_div:
                paragraphs = content_div.find_all("p")
                content_markdown = "\n\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            else:
                paragraphs = soup.find_all("p")
                content_markdown = "\n\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                
        return {
            "url": url,
            "title": title.strip(),
            "date_crawled": datetime.now().isoformat(),
            "content_markdown": content_markdown.strip()
        }
    except Exception as fallback_err:
        print(f"  -> Fallback also failed: {fallback_err}")
        raise fallback_err


async def crawl_all():
    """Crawl toàn bộ bài báo trong ARTICLE_URLS."""
    setup_directory()

    for i, url in enumerate(ARTICLE_URLS, 1):
        print(f"[{i}/{len(ARTICLE_URLS)}] Crawling: {url}")
        article = await crawl_article(url)

        # Lưu file JSON
        filename = f"article_{i:02d}.json"
        filepath = DATA_DIR / filename
        filepath.write_text(json.dumps(article, ensure_ascii=False, indent=2))
        print(f"  ✓ Saved: {filepath}")


if __name__ == "__main__":
    if not ARTICLE_URLS:
        print("⚠ Hãy điền ARTICLE_URLS trước khi chạy!")
        print("Gợi ý: tìm bài báo trên VnExpress, Tuổi Trẻ, Thanh Niên, ...")
    else:
        asyncio.run(crawl_all())
