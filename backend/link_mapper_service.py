import httpx
import logging
import re
from bs4 import BeautifulSoup
from typing import Optional

_LOGGER = logging.getLogger(__name__)

class LinkMapperService:
    def __init__(self):
        self.client = httpx.AsyncClient(follow_redirects=True)

    async def map_to_deep_link(self, motn_url: str) -> str:
        """
        Maps a MOTN URL to a specific Apple TV deep link by parsing the provider's page.
        """
        _LOGGER.info(f"Mapping URL: {motn_url}")
        
        if "amazon.com" in motn_url or "primevideo.com" in motn_url:
            return await self._map_prime_video(motn_url)
        
        # Add other providers here as needed
        
        # Fallback to the original URL if no specific mapper is found
        return motn_url

    async def _map_prime_video(self, url: str) -> str:
        """
        Parses a Prime Video page to extract the content ID and construct an Apple TV deep link.
        """
        try:
            _LOGGER.info(f"Fetching Prime Video page: {url}")
            # Prime Video sometimes blocks standard scrapers, so we use a realistic User-Agent
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Look for <link rel="canonical" href="...">
            canonical_link = soup.find('link', rel='canonical')
            if canonical_link and canonical_link.get('href'):
                href = canonical_link['href']
                _LOGGER.info(f"Found canonical link: {href}")
                
                # Extract ID after /dp/ (usually starts with B0)
                match = re.search(r'/dp/([A-Z0-9]{10})', href)
                if match:
                    content_id = match.group(1)
                    _LOGGER.info(f"Extracted Prime Video ID: {content_id}")
                    
                    # Construct Apple TV deep link for Prime Video
                    # Based on common URL schemes for Prime Video on tvOS
                    # Usually: aiv://aiv/play?asin=[ID] or just the https link which Apple TV intercepts
                    # For now, let's return the https link that the TV app likes
                    return f"https://watch.amazon.com/watch?asin={content_id}"

            _LOGGER.warning("Could not find canonical link or ID on Prime Video page.")
            return url

        except Exception as e:
            _LOGGER.error(f"Failed to map Prime Video URL: {e}")
            return url

# Global instance
link_mapper_service = LinkMapperService()
