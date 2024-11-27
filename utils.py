import logging
from lxml import html
from urllib.parse import urlparse, urljoin
import aiohttp


def is_internal_link(base_url, link):
    base_domain = urlparse(base_url).netloc
    link_domain = urlparse(link).netloc
    return base_domain == link_domain or not link_domain


def is_valid_link(link):
    if not link.lower().startswith('https://'):
        return False
    
    return True

async def fetch_links(url, session, timeout):
    try:
        async with session.get(url, timeout=timeout) as response:
            if response.status != 200:
                logging.warning(f"Failed to fetch {url}: {response.status}")
                return []
            text = await response.text()
            tree = html.fromstring(text)
            tree.make_links_absolute(url)
            page_title = tree.xpath('//title/text()')
            page_title = page_title[0].strip() if page_title else "No title"
            
            logging.info(f"PAGE: Processing page: {page_title} ({url})")
            
            links = [
                {"title": element.text_content().strip(), "url": element.get("href")}
                for element in tree.xpath('//a[@href]')
                if element.get("href")
                and is_internal_link(url, element.get("href"))
                and is_valid_link(element.get("href"))
            ]

            return links
    except Exception as e:
        logging.error(f"Error fetching {url}: {e}")
        return []
