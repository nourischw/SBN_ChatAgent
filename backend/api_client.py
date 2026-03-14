"""
Internal API Client for SBN ChatAgent
Handles communication with company's internal APIs
"""
import httpx
import os
from typing import Optional, Dict, Any, List

try:
    from .models import Product
except ImportError:
    from models import Product


class InternalAPIClient:
    """Client for internal company APIs"""

    def __init__(self):
        self.base_url = os.getenv("INTERNAL_API_URL", "http://localhost:8000")
        self.timeout = 10.0  # Reduced timeout

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

            print(f"[API Client] Fetching products from: {self.base_url}/api/products")
            print(f"[API Client] Headers: {headers}")
            print(f"[API Client] Params: {params}")

            try:
                response = await client.get(
                    f"{self.base_url}/api/products",
                    headers=headers,
                    params=params,
                    timeout=self.timeout
                )
                print(f"[API Client] Response status: {response.status_code}")
                print(f"[API Client] Response body: {response.text[:500]}")
                response.raise_for_status()
                data = response.json()

                # Handle different response formats
                if isinstance(data, list):
                    products = [Product(**item) for item in data]
                    print(f"[API Client] Parsed {len(products)} products (list format)")
                    return products
                elif isinstance(data, dict) and "data" in data:
                    products = [Product(**item) for item in data["data"]]
                    print(f"[API Client] Parsed {len(products)} products (data field)")
                    return products
                elif isinstance(data, dict) and "items" in data:
                    products = [Product(**item) for item in data["items"]]
                    print(f"[API Client] Parsed {len(products)} products (items field)")
                    return products
                else:
                    print(f"[API Client] Unknown response format: {type(data)}")
                    return []
            except httpx.HTTPError as e:
                print(f"[API Client] HTTP Error fetching product list: {e}")
                return []
            except Exception as e:
                print(f"[API Client] Unexpected error: {e}")
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
