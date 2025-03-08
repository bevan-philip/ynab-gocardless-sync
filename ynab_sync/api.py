import httpx
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# Configure logging
logger = logging.getLogger(__name__)

def log_and_raise_for_status(response: httpx.Response) -> None:
    """
    Check the response status and raise an exception if needed.
    If the response indicates an error, log the response content before raising.
    """
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        # Log the error with detailed information
        logger.error(
            f"HTTP Error: {e.response.status_code} {e.response.reason_phrase}\n"
            f"Request URL: {e.response.url}\n"
            f"Request Method: {e.response.request.method}\n"
            f"Request Headers: {e.response.request.headers}\n"
            f"Response Headers: {e.response.headers}\n"
            f"Response Content: {e.response.text}"
        )
        # Re-raise the exception
        raise

@dataclass
class YNABClient:
    api_key: str
    BASE_URL: str = "https://api.ynab.com/v1"

    headers: Dict[str, str] = field(init=False)
    client: httpx.AsyncClient = field(default_factory=httpx.AsyncClient(timeout=None))

    def __post_init__(self):
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_transactions(self, budget_id: str, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create transactions in YNAB."""
        async with self.client as client:
            response = await client.post(
                f"{self.BASE_URL}/budgets/{budget_id}/transactions",
                headers=self.headers,
                json={"transactions": transactions}
            )
            log_and_raise_for_status(response)
            return response.json()

@dataclass
class GoCardlessClient:
    secret_id: str
    secret_key: str

    BASE_URL: str = "https://bankaccountdata.gocardless.com/api/v2"
    headers: Dict[str, str] = field(default_factory=lambda: { "Content-Type": "application/json" })
    client: httpx.AsyncClient = field(default_factory=httpx.AsyncClient(timeout=None))

    def __post_init__(self):
        self.get_access_token()

    async def get_access_token(self) -> None:
        """Get a new access token using the secret credentials."""
        async with self.client as client:
            response = await client.post(
                f"{self.BASE_URL}/token/new/",
                headers=self.headers,
                json={
                    "secret_id": self.secret_id,
                    "secret_key": self.secret_key
                }
            )
            log_and_raise_for_status(response)
            data = response.json()
            self.headers["Authorization"] = f"Bearer {data['access']}"

    async def get_institutions(self, country_code: str = "gb") -> List[Dict[str, Any]]:
        """Get list of available financial institutions for a country."""
            
        async with self.client as client:
            response = await client.get(
                f"{self.BASE_URL}/institutions/",
                headers=self.headers,
                params={"country": country_code}
            )
            log_and_raise_for_status(response)
            return response.json()

    async def create_end_user_agreement(
        self,
        institution_id: str,
        max_historical_days: Optional[int] = None,
        access_valid_for_days: Optional[int] = None,
        access_scope: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create an end user agreement with custom terms."""
            
        payload = {"institution_id": institution_id}
        if max_historical_days:
            payload["max_historical_days"] = max_historical_days
        if access_valid_for_days:
            payload["access_valid_for_days"] = access_valid_for_days
        if access_scope:
            payload["access_scope"] = access_scope

        async with self.client as client:
            response = await client.post(
                f"{self.BASE_URL}/agreements/enduser/",
                headers=self.headers,
                json=payload
            )
            log_and_raise_for_status(response)
            return response.json()

    async def create_requisition(
        self,
        redirect_url: str,
        institution_id: str,
        reference: Optional[str] = None,
        agreement_id: Optional[str] = None,
        user_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a requisition for account linking."""
            
        payload = {
            "redirect": redirect_url,
            "institution_id": institution_id
        }
        if reference:
            payload["reference"] = reference
        if agreement_id:
            payload["agreement"] = agreement_id
        if user_language:
            payload["user_language"] = user_language

        print("we about to create a requisition")

        async with self.client as client:
            response = await client.post(
                f"{self.BASE_URL}/requisitions/",
                headers=self.headers,
                json=payload
            )
            log_and_raise_for_status(response)
            return response.json()

    async def get_requisition(self, requisition_id: str) -> Dict[str, Any]:
        """Get details of a specific requisition."""
            
        async with self.client as client:
            response = await client.get(
                f"{self.BASE_URL}/requisitions/{requisition_id}/",
                headers=self.headers
            )
            log_and_raise_for_status(response)
            return response.json()

    async def get_account_transactions(self, account_id: str, date_from: Optional[str] = None) -> Dict[str, Any]:
        """Get transactions for a specific account.
        
        Args:
            account_id: The ID of the account to get transactions for
            date_from: Optional ISO 8601 format date to filter transactions from
        """
            
        params = {}
        if date_from:
            params["date_from"] = date_from

        async with self.client as client:
            response = await client.get(
                f"{self.BASE_URL}/accounts/{account_id}/transactions/",
                headers=self.headers,
                params=params
            )
            log_and_raise_for_status(response)
            return response.json()

    async def get_account_details(self, account_id: str) -> Dict[str, Any]:
        """Get details for a specific account."""
            
        async with self.client as client:
            response = await client.get(
                f"{self.BASE_URL}/accounts/{account_id}/",
                headers=self.headers
            )
            log_and_raise_for_status(response)
            return response.json()

    async def get_account_balances(self, account_id: str) -> Dict[str, Any]:
        """Get balances for a specific account."""
            
        async with self.client as client:
            response = await client.get(
                f"{self.BASE_URL}/accounts/{account_id}/balances/",
                headers=self.headers
            )
            log_and_raise_for_status(response)
            return response.json()
