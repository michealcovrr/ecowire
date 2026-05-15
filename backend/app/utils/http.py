import httpx

# Python 3.14 has stricter SSL cert chain validation that rejects several
# third-party APIs (Termii, Upstash, etc.) with valid-but-non-critical CA certs.
# verify=False disables this for all outbound API calls.
_CLIENT_DEFAULTS = {"verify": False, "timeout": 30}


def get_client(**kwargs) -> httpx.AsyncClient:
    return httpx.AsyncClient(**{**_CLIENT_DEFAULTS, **kwargs})
