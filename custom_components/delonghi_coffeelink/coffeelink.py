"""Async client for the De'Longhi Coffee Link cloud (Gigya + Ayla).

Reverse-engineered from the it.delonghi Android app. The Gigya API key and the
Ayla app_id/app_secret below are the app's own hardcoded values — identical for
every user, not personal secrets. End users only provide email + password.

Auth chain (fully headless, no app/emulator needed at runtime):
  1. Gigya accounts.login  (loginID + password + apiKey)  -> id_token (in response)
  2. Ayla  token_sign_in   (app_id + app_secret + token)   -> access_token (24h)
Commands are raw ECAM frames (base64) written to the `app_data_request` property.
"""
from __future__ import annotations

import base64
import logging
import struct
import time

import aiohttp

_LOGGER = logging.getLogger(__name__)

# --- App-level constants (same for all users) --------------------------------
GIGYA_API_KEY = "4_DRIMLu7jk9bkKwpRRoQOuw"
AYLA_APP_ID = "DLonghiCoffeeIdKit-sQ-id"
AYLA_APP_SECRET = "DLonghiCoffeeIdKit-HT6b0VNd4y6CSha9ivM5k8navLw"

# Stock Android okhttp UA — Ayla identifies the app by app_id/secret, not UA.
USER_AGENT = "Dalvik/2.1.0 (Linux; U; Android 14; Pixel 7 Build/UP1A.231005.007)"

# Region -> endpoints. EU is verified against a live account; US/CN endpoints
# are the standard Ayla/Gigya hosts and may need a region-specific Gigya key.
REGIONS: dict[str, dict[str, str]] = {
    "eu": {
        "gigya": "https://accounts.eu1.gigya.com",
        "ayla_user": "https://user-field-eu.aylanetworks.com",
        "ayla_ads": "https://ads-eu.aylanetworks.com",
    },
    "us": {
        "gigya": "https://accounts.us1.gigya.com",
        "ayla_user": "https://user-field.aylanetworks.com",
        "ayla_ads": "https://ads-field.aylanetworks.com",
    },
    "cn": {
        "gigya": "https://accounts.cn1.sapcdm.cn",
        "ayla_user": "https://user-field.ayla.com.cn",
        "ayla_ads": "https://ads-field.ayla.com.cn",
    },
}

# Captured ECAM "turn on / wake from standby" frame (base64):
#   0d 07 84 0f 02 01 55 12 | 6a 82 1b e3 | 57 2e 8c 4d
#   └─ ECAM cmd 84 0f "ON" ─┘  └ ts (4B) ┘  └ session (4B) ┘
# The ECAM frame is length-delimited (byte 1 = len); the trailing 8 bytes are the
# app's own timestamp + per-session token appended after the frame. We refresh the
# timestamp on send so it isn't stale; the machine parses only the ECAM portion.
WAKE_FRAME = "DQeEDwIBVRJqghvjVy6MTQ=="
_WAKE_TS_OFFSET = 8


class AuthError(Exception):
    """Raised when authentication fails (bad credentials / region)."""


class CoffeeLinkError(Exception):
    """Raised for transport / API errors."""


def refresh_frame_timestamp(frame_b64: str) -> str:
    """Rewrite the 4-byte app timestamp inside an app_data_request frame."""
    b = bytearray(base64.b64decode(frame_b64))
    if len(b) >= _WAKE_TS_OFFSET + 4:
        b[_WAKE_TS_OFFSET:_WAKE_TS_OFFSET + 4] = struct.pack(">I", int(time.time()))
    return base64.b64encode(bytes(b)).decode()


def decode_monitor(value: str | None) -> dict:
    """Decode d302_monitor_machine into a small status dict.

    Frame: d0 12 75 0f 00 <flags> ...  byte 5 carries the power/heat state:
      bit 0x80 = powered on, bit 0x04 = heating up.
    """
    out: dict = {"raw": value, "power_state": "unknown"}
    if not value:
        return out
    try:
        b = base64.b64decode(value)
    except Exception:  # noqa: BLE001
        return out
    if len(b) < 6:
        return out
    flags = b[5]
    out["flags"] = flags
    if flags & 0x04:
        out["power_state"] = "heating"
    elif flags & 0x80:
        out["power_state"] = "ready"
    else:
        out["power_state"] = "standby"
    return out


class CoffeeLinkClient:
    """Minimal async Gigya+Ayla client for one De'Longhi account."""

    def __init__(self, session: aiohttp.ClientSession, email: str,
                 password: str, region: str = "eu") -> None:
        self._session = session
        self._email = email
        self._password = password
        self._region = region if region in REGIONS else "eu"
        self._ep = REGIONS[self._region]
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self._expires_at: float = 0.0
        self.dsn: str | None = None
        self.device: dict | None = None

    # -- low-level -------------------------------------------------------------
    async def _request(self, method: str, url: str, *, data=None, json=None,
                       headers=None) -> tuple[int, dict | str]:
        hdrs = {"Accept": "application/json", "User-Agent": USER_AGENT}
        if headers:
            hdrs.update(headers)
        try:
            async with self._session.request(
                method, url, data=data, json=json, headers=hdrs,
                timeout=aiohttp.ClientTimeout(total=25),
            ) as resp:
                text = await resp.text()
                try:
                    body: dict | str = await resp.json(content_type=None)
                except Exception:  # noqa: BLE001
                    body = text
                return resp.status, body
        except aiohttp.ClientError as err:
            raise CoffeeLinkError(f"HTTP error for {url}: {err}") from err

    # -- auth ------------------------------------------------------------------
    async def _gigya_login(self) -> str:
        url = f"{self._ep['gigya']}/accounts.login?apiKey={GIGYA_API_KEY}&httpStatusCodes=true"
        status, body = await self._request("POST", url, data={
            "loginID": self._email,
            "password": self._password,
            "targetEnv": "mobile",
            "include": "id_token,profile,data, preferences",
            "sessionExpiration": "7776000",
        })
        if not isinstance(body, dict) or body.get("errorCode") != 0:
            msg = body.get("errorMessage") if isinstance(body, dict) else str(body)[:120]
            raise AuthError(f"Gigya login failed: {msg}")
        id_token = body.get("id_token")
        if not id_token:
            raise AuthError("Gigya login response missing id_token")
        return id_token

    async def _ayla_sign_in(self, id_token: str) -> None:
        url = f"{self._ep['ayla_user']}/api/v1/token_sign_in"
        status, body = await self._request("POST", url, data={
            "app_id": AYLA_APP_ID,
            "app_secret": AYLA_APP_SECRET,
            "token": id_token,
        })
        if not isinstance(body, dict) or "access_token" not in body:
            raise AuthError(f"Ayla token_sign_in failed: {str(body)[:120]}")
        self._store_tokens(body)

    def _store_tokens(self, body: dict) -> None:
        self.access_token = body["access_token"]
        self.refresh_token = body.get("refresh_token", self.refresh_token)
        self._expires_at = time.monotonic() + int(body.get("expires_in", 86400)) - 120

    async def authenticate(self) -> None:
        """Full login: Gigya -> id_token -> Ayla access_token."""
        id_token = await self._gigya_login()
        await self._ayla_sign_in(id_token)

    async def _refresh(self) -> None:
        if not self.refresh_token:
            await self.authenticate()
            return
        url = f"{self._ep['ayla_user']}/users/refresh_token.json"
        status, body = await self._request(
            "POST", url, json={"user": {"refresh_token": self.refresh_token}}
        )
        if isinstance(body, dict) and body.get("access_token"):
            self._store_tokens(body)
        else:
            # refresh token rejected/expired -> full re-auth
            await self.authenticate()

    async def async_ensure_token(self) -> None:
        if not self.access_token:
            await self.authenticate()
        elif time.monotonic() >= self._expires_at:
            await self._refresh()

    # -- device ----------------------------------------------------------------
    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"auth_token {self.access_token}"}

    async def async_get_devices(self) -> list[dict]:
        await self.async_ensure_token()
        url = f"{self._ep['ayla_ads']}/apiv1/devices.json"
        status, body = await self._request("GET", url, headers=self._auth_headers())
        if status == 401:
            await self._refresh()
            status, body = await self._request("GET", url, headers=self._auth_headers())
        if not isinstance(body, list):
            raise CoffeeLinkError(f"unexpected devices payload: {str(body)[:120]}")
        return [d.get("device", d) for d in body]

    async def async_pick_dsn(self) -> str:
        await self.async_get_device()
        return self.dsn

    async def async_get_device(self) -> dict:
        """Return (and cache) the first device dict on the account."""
        devices = await self.async_get_devices()
        if not devices:
            raise CoffeeLinkError("no device found on this account")
        self.device = devices[0]
        self.dsn = self.device.get("dsn")
        return self.device

    async def async_get_properties(self) -> dict[str, object]:
        await self.async_ensure_token()
        if not self.dsn:
            await self.async_pick_dsn()
        url = f"{self._ep['ayla_ads']}/apiv1/dsns/{self.dsn}/properties.json"
        status, body = await self._request("GET", url, headers=self._auth_headers())
        if status == 401:
            await self._refresh()
            status, body = await self._request("GET", url, headers=self._auth_headers())
        if not isinstance(body, list):
            raise CoffeeLinkError(f"unexpected properties payload: {str(body)[:120]}")
        return {
            p["property"]["name"]: p["property"].get("value")
            for p in body if "property" in p
        }

    async def async_device_online(self) -> bool:
        devices = await self.async_get_devices()
        if not devices:
            return False
        return str(devices[0].get("connection_status", "")).lower() == "online"

    async def async_write_datapoint(self, prop: str, value: str) -> None:
        await self.async_ensure_token()
        if not self.dsn:
            await self.async_pick_dsn()
        url = f"{self._ep['ayla_ads']}/apiv1/dsns/{self.dsn}/properties/{prop}/datapoints.json"
        headers = self._auth_headers()
        headers["Content-Type"] = "application/json"
        status, body = await self._request(
            "POST", url, json={"datapoint": {"value": value}}, headers=headers
        )
        if status == 401:
            await self._refresh()
            headers = self._auth_headers()
            headers["Content-Type"] = "application/json"
            status, body = await self._request(
                "POST", url, json={"datapoint": {"value": value}}, headers=headers
            )
        if status not in (200, 201):
            raise CoffeeLinkError(f"datapoint write {prop} failed: HTTP {status} {str(body)[:120]}")

    async def async_wake(self) -> None:
        """Power on / wake the machine from standby."""
        await self.async_write_datapoint("app_data_request", refresh_frame_timestamp(WAKE_FRAME))
