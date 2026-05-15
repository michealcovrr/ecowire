import asyncio
import json
from app.config import get_settings
from app.services.otp_service import normalise_phone
import httpx

async def main():
    settings = get_settings()
    phone = normalise_phone("07040684933")
    print(f"Testing WATI Template for {phone}...")
    
    headers = {
        "Authorization": f"Bearer {settings.wati_token}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "template_name": "econet_otp",
        "broadcast_name": f"otp_{phone[-6:]}",
        "parameters": [{"name": "1", "value": "123456"}],
    }
    
    async with httpx.AsyncClient(verify=False, timeout=15) as client:
        resp = await client.post(
            f"{settings.wati_api_url}/api/v1/sendTemplateMessage",
            json=payload,
            params={"whatsappNumber": phone},
            headers=headers,
        )
        
    print(resp.status_code)
    try:
        print(json.dumps(resp.json(), indent=2))
    except:
        print(resp.text)

if __name__ == "__main__":
    asyncio.run(main())
