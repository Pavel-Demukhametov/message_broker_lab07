import logging
from urllib.parse import urlparse, urljoin
import aiohttp
from bs4 import BeautifulSoup

def is_internal_link(base_url, link):
    base_domain = urlparse(base_url).netloc
    link_domain = urlparse(link).netloc
    return base_domain == link_domain or not link_domain

def is_valid_link(link):
    return link.lower().startswith('https://')

async def fetch_links(url, session, timeout):
    try:
        async with session.get(url, timeout=timeout) as response:
            if response.status != 200:
                logging.warning(f"Failed to fetch {url}: {response.status}")
                return []
            text = await response.text()
            
            soup = BeautifulSoup(text, 'html.parser')
            page_title = soup.title.string.strip() if soup.title else "No title"
            
            logging.info(f"PAGE: Processing page: {page_title} ({url})")
            
            links = [
                {"title": link.get_text(strip=True), "url": urljoin(url, link.get('href'))}
                for link in soup.find_all('a', href=True)
                if is_internal_link(url, urljoin(url, link.get('href'))) and is_valid_link(urljoin(url, link.get('href')))
            ]

            return links
    except Exception as e:
        logging.error(f"Error fetching {url}: {e}")
        return []
