import aiohttp
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class CryptoBotClient:
    def __init__(self, api_token: str, testnet: bool = False):
        self.api_token = api_token
        # Corrected base URLs from documentation
        self.base_url = "https://testnet-pay.crypt.bot/api" if testnet else "https://pay.crypt.bot/api"
        self.headers = {"Crypto-Pay-API-Token": api_token}

    async def _request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Any:
        url = f"{self.base_url}/{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=self.headers, json=data, params=params) as response:
                result = await response.json()
                if not result.get("ok"):
                    logger.error(f"CryptoBot API error: {result}")
                    # Handle error code and description if present
                    error = result.get("error", {})
                    error_msg = f"{error.get('code')}: {error.get('name')}" if isinstance(error, dict) else str(error)
                    raise Exception(f"CryptoBot API error: {error_msg}")
                return result.get("result")

    async def get_me(self) -> Dict:
        """Returns basic information about the bot."""
        return await self._request("GET", "getMe")

    async def create_invoice(
        self, 
        amount: float, 
        asset: str = "USDT", 
        description: Optional[str] = None,
        payload: Optional[str] = None
    ) -> Dict:
        """
        Creates a new invoice.
        :param amount: Amount of the invoice in float.
        :param asset: Cryptocurrency alphabetic code.
        :param description: Description for the invoice.
        :param payload: Any data you want to attach to the invoice.
        """
        data = {
            "asset": asset,
            "amount": str(amount),
            "description": description,
            "payload": payload,
            "allow_anonymous": False
        }
        # Filter out None values
        data = {k: v for k, v in data.items() if v is not None}
        return await self._request("POST", "createInvoice", data)

    async def get_invoices(
        self, 
        invoice_ids: Optional[List[int]] = None, 
        status: Optional[str] = None,
        count: int = 100
    ) -> List[Dict]:
        """
        Retrieves invoices created by your app.
        :param invoice_ids: List of invoice IDs.
        :param status: Filter invoices by status (active, paid).
        """
        params = {"count": count}
        if invoice_ids:
            params["invoice_ids"] = ",".join(map(str, invoice_ids))
        if status:
            params["status"] = status
            
        return await self._request("GET", "getInvoices", params=params)