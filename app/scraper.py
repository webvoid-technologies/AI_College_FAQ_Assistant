import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin, urlparse, urldefrag
from typing import List, Dict, Set
import os

SKIP_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico', '.bmp',
    '.css', '.js', '.xml', '.json', '.zip', '.rar', '.mp4', '.mp3',
    '.avi', '.mov', '.woff', '.woff2', '.ttf', '.eot', '.doc', '.docx',
    '.xls', '.xlsx', '.ppt', '.pptx'
}
PDF_EXTENSION = '.pdf'

class MJRCETScraper:
    def __init__(self, base_url: str = "https://www.mjrcet.org/"):
        self.base_url = base_url
        self.visited_urls: Set[str] = set()
        self.college_data: List[Dict] = []
        self.pdf_links: Set[str] = set()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def is_valid_url(self, url: str) -> bool:
        """Check if URL belongs to MJRCET domain"""
        parsed = urlparse(url)
        return 'mjrcet.org' in parsed.netloc

    def url_extension(self, url: str) -> str:
        """Return lowercase file extension of the URL path"""
        path = urlparse(url).path
        return os.path.splitext(path)[1].lower()

    def is_html_url(self, url: str) -> bool:
        """Check if URL likely points to an HTML page"""
        ext = self.url_extension(url)
        return ext not in SKIP_EXTENSIONS and ext != PDF_EXTENSION
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        return ' '.join(text.split()).strip()
    
    def scrape_page(self, url: str) -> Dict:
        """Scrape a single page"""
        try:
            print(f"Scraping: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            if 'text/html' not in response.headers.get('Content-Type', ''):
                print(f"Skipped (non-HTML): {url}")
                return None

            soup = BeautifulSoup(response.content, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text() if title else url
            
            # Extract main content
            content_areas = soup.find_all(['article', 'main', 'div'], class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['content', 'main', 'article', 'body']
            ))
            
            if not content_areas:
                content_areas = [soup.find('body')]
            
            # Extract text content
            text_content = []
            for area in content_areas:
                if area:
                    # Get headings
                    headings = area.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    for heading in headings:
                        text = self.clean_text(heading.get_text())
                        if text and len(text) > 3:
                            text_content.append(f"## {text}")
                    
                    # Get paragraphs
                    paragraphs = area.find_all(['p', 'li', 'td'])
                    for p in paragraphs:
                        text = self.clean_text(p.get_text())
                        if text and len(text) > 20:
                            text_content.append(text)
            
            # Extract tables
            tables = soup.find_all('table')
            table_data = []
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    row_text = ' | '.join([self.clean_text(cell.get_text()) for cell in cells])
                    if row_text:
                        table_data.append(row_text)
            
            # Combine all content
            full_content = '\n'.join(text_content + table_data)
            
            # Extract links for further crawling
            links = []
            for link in soup.find_all('a', href=True):
                absolute_url = urldefrag(urljoin(url, link['href']))[0]
                if not self.is_valid_url(absolute_url) or absolute_url in self.visited_urls:
                    continue
                if self.url_extension(absolute_url) == PDF_EXTENSION:
                    self.pdf_links.add(absolute_url)
                    continue
                if self.is_html_url(absolute_url):
                    links.append(absolute_url)
            
            return {
                'url': url,
                'title': self.clean_text(title_text),
                'content': full_content,
                'links': links
            }
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None
    
    def scrape_website(self, max_pages: int = 50, delay: float = 1.0):
        """Scrape multiple pages from the website"""
        urls_to_visit = [self.base_url]
        
        # Important sections to prioritize (actual pages on mjrcet.org)
        priority_paths = [
            '/aboutmjr.php',
            '/admissions.php',
            '/reg.php',
            '/sch.php',
            '/pay.php',
            '/syl.php',
            '/placement.php',
            '/cse_dpt.php',
            '/ece_dpt.php',
            '/eee_dpt.php',
            '/mech_dpt.php',
            '/civil_dpt.php',
            '/h&s_dept.php',
            '/campus.php',
            '/hostels.php',
            '/transport.php',
            '/about_library.php',
            '/contact.php',
            '/nirf.php',
            '/principal.php',
            '/director.php'
        ]
        
        # Add priority URLs
        for path in priority_paths:
            urls_to_visit.append(urljoin(self.base_url, path))
        
        pages_scraped = 0
        
        while urls_to_visit and pages_scraped < max_pages:
            url = urls_to_visit.pop(0)
            
            if url in self.visited_urls:
                continue
            
            self.visited_urls.add(url)
            page_data = self.scrape_page(url)
            
            if page_data and page_data['content']:
                self.college_data.append({
                    'url': page_data['url'],
                    'title': page_data['title'],
                    'content': page_data['content']
                })
                
                # Add new links to visit
                for link in page_data['links'][:20]:  # Limit links per page
                    if link not in self.visited_urls and link not in urls_to_visit:
                        urls_to_visit.append(link)

                pages_scraped += 1
                print(f"Progress: {pages_scraped}/{max_pages} pages scraped")

            time.sleep(delay)  # Be respectful to the server

        # Index discovered PDFs as reference stubs
        for pdf_url in sorted(self.pdf_links):
            name = os.path.basename(urlparse(pdf_url).path)
            title = os.path.splitext(name)[0].replace('_', ' ').replace('-', ' ')
            self.college_data.append({
                'url': pdf_url,
                'title': f'{title} (PDF)',
                'content': f'PDF document "{title}" available at {pdf_url}'
            })

        return self.college_data
    
    def save_data(self, filepath: str):
        """Save scraped data to JSON file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.college_data, f, indent=2, ensure_ascii=False)
        print(f"Data saved to {filepath}")
    
    def load_data(self, filepath: str) -> List[Dict]:
        """Load scraped data from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"File not found: {filepath}")
            return []


def main():
    """Main function to run the scraper"""
    scraper = MJRCETScraper()
    
    print("Starting MJRCET website scraping...")
    print("This may take a few minutes...\n")
    
    data = scraper.scrape_website(max_pages=80, delay=0.5)
    
    print(f"\nScraping completed!")
    print(f"Total pages scraped: {len(data)}")
    
    # Save data
    scraper.save_data('./data/scraped_data.json')
    
    # Print sample
    if data:
        print("\nSample data:")
        print(f"Title: {data[0]['title']}")
        print(f"Content preview: {data[0]['content'][:200]}...")


if __name__ == "__main__":
    main()
