import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional

class YNABClient:
    BASE_URL = "https://api.ynab.com/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_transactions(self, budget_id: str, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create transactions in YNAB."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/budgets/{budget_id}/transactions",
                headers=self.headers,
                json={"transactions": transactions}
            )
            response.raise_for_status()
            return response.json()

class GoCardlessClient:
    BASE_URL = "https://bankaccountdata.gocardless.com/api/v2"
    
    def __init__(self, secret_id: str, secret_key: str):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.access_token = None
        self.headers = {
            "Content-Type": "application/json"
        }
    
    async def get_access_token(self) -> str:
        """Get a new access token using the secret credentials."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/token/new/",
                headers=self.headers,
                json={
                    "secret_id": self.secret_id,
                    "secret_key": self.secret_key
                }
            )
            response.raise_for_status()
            data = response.json()
            self.access_token = data["access"]
            self.headers["Authorization"] = f"Bearer {self.access_token}"
            return self.access_token

    async def get_institutions(self, country_code: str = "gb") -> List[Dict[str, Any]]:
        """Get list of available financial institutions for a country."""
        if not self.access_token:
            await self.get_access_token()
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/institutions/",
                headers=self.headers,
                params={"country": country_code}
            )
            response.raise_for_status()
            return response.json()

    async def create_end_user_agreement(
        self,
        institution_id: str,
        max_historical_days: Optional[int] = None,
        access_valid_for_days: Optional[int] = None,
        access_scope: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create an end user agreement with custom terms."""
        if not self.access_token:
            await self.get_access_token()
            
        payload = {"institution_id": institution_id}
        if max_historical_days:
            payload["max_historical_days"] = max_historical_days
        if access_valid_for_days:
            payload["access_valid_for_days"] = access_valid_for_days
        if access_scope:
            payload["access_scope"] = access_scope

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/agreements/enduser/",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
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
        if not self.access_token:
            await self.get_access_token()
            
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

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/requisitions/",
                headers=self.headers,
                json=payload
            )
            print(f"{response.json()=}")
            response.raise_for_status()
            return response.json()

    async def get_requisition(self, requisition_id: str) -> Dict[str, Any]:
        """Get details of a specific requisition."""
        if not self.access_token:
            await self.get_access_token()
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/requisitions/{requisition_id}/",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_account_transactions(self, account_id: str) -> Dict[str, Any]:
        """Get transactions for a specific account."""
        if not self.access_token:
            await self.get_access_token()
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/accounts/{account_id}/transactions/",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json() 