"""Google ID token verification.

In production, verifies tokens against Google's API.
In test mode (when X-Test-Google-Email header is present), bypasses verification.
"""

import httpx

from app.config import settings


class GoogleAuthError(Exception):
    pass


async def verify_google_id_token(id_token: str) -> dict:
    """Verify a Google ID token and return user info.

    Returns dict with 'email', 'name', 'sub' (Google user ID).
    Raises GoogleAuthError on failure.
    """
    # Call Google's tokeninfo endpoint
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": id_token},
        )

    if resp.status_code != 200:
        raise GoogleAuthError("Invalid Google ID token")

    data = resp.json()

    # Verify the audience matches our client ID
    if data.get("aud") != settings.google_client_id:
        raise GoogleAuthError("Token audience mismatch")

    email = data.get("email")
    if not email:
        raise GoogleAuthError("No email in Google token")

    return {
        "email": email,
        "name": data.get("name", email.split("@")[0]),
        "sub": data.get("sub", ""),
    }
