"""
Internal API Client for SBN ChatAgent
Handles communication with company's internal APIs
"""
import httpx
import os
import logging
from typing import Optional, Dict, Any, List

try:
    from .models import Product
    from .config import settings
except ImportError:
    from models import Product
    from config import settings

logger = logging.getLogger(__name__)


class InternalAPIClient:
    """Client for internal company APIs"""

    def __init__(self):
        self.base_url = settings.internal_api_url
        self.timeout = settings.internal_api_timeout

    async def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        return {
            "Content-Type": "application/json"
        }

    async def get_product_list(
        self,
        lang: str = "English",
        currency: str = "HKD"
    ) -> List[Product]:
        """Fetch product list from internal API"""
        async with httpx.AsyncClient() as client:
            params = {"Lang": lang, "Currency": currency}
            headers = await self._get_headers()

            logger.debug(f"Fetching products from: {self.base_url}/api/products")
            logger.debug(f"Headers: {headers}")
            logger.debug(f"Params: {params}")

            try:
                response = await client.get(
                    f"{self.base_url}/api/products",
                    headers=headers,
                    params=params,
                    timeout=self.timeout
                )
                logger.debug(f"Response status: {response.status_code}")
                response.raise_for_status()
                data = response.json()

                # Handle different response formats
                if isinstance(data, list):
                    products = [Product(**item) for item in data]
                    logger.info(f"Parsed {len(products)} products (list format)")
                    return products
                elif isinstance(data, dict) and "data" in data:
                    products = [Product(**item) for item in data["data"]]
                    logger.info(f"Parsed {len(products)} products (data field)")
                    return products
                elif isinstance(data, dict) and "items" in data:
                    products = [Product(**item) for item in data["items"]]
                    logger.info(f"Parsed {len(products)} products (items field)")
                    return products
                else:
                    logger.warning(f"Unknown response format: {type(data)}")
                    return []
            except httpx.HTTPError as e:
                logger.error(f"HTTP Error fetching product list: {e}")
                return []
            except Exception as e:
                logger.error(f"Unexpected error fetching product list: {e}")
                return []

    async def health_check(self) -> bool:
        """Check if internal API is available"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/health",
                    headers=await self._get_headers(),
                    timeout=5.0
                )
                return response.status_code == 200
            except Exception:
                return False
