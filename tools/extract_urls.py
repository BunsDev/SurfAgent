import re
from urllib.parse import urlparse
from typing import List
from config.log import logger
from tools.host_tracker import host_tracker 

def extract_urls_from_search_results(search_text: str) -> List[str]:
    urls = re.findall(r'(https?://[^\s\'"]+)', search_text)
    valid_urls = []
    for url in urls:
        url = re.sub(r'[.,)\]]+$', '', url)
        if url.startswith(('http://', 'https://')):
            if not host_tracker.is_problematic_host(url):
                valid_urls.append(url)
            else:
                logger.info(f"Filtered out problematic host: {urlparse(url).netloc}")
    return list(set(valid_urls))