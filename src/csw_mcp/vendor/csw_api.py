#!/usr/bin/env python3
"""
Cisco Secure Workload (CSW / Tetration) API client with HMAC digest authentication.

Compatible with: CSW SaaS clusters and on-prem Tetration appliances.

Usage:
    python3 csw_api.py GET /openapi/v1/app_scopes
    python3 csw_api.py GET /openapi/v1/sensors
    python3 csw_api.py POST /openapi/v1/inventory/search '{"filter": {...}}'
    python3 csw_api.py GET /openapi/v1/sensors --limit 100 --offset 0

Environment variables (set in .env or export before running):
    CSW_API_URL    - Cluster base URL e.g. https://your-cluster.tetrationcloud.com
    CSW_API_KEY    - API key (hex string from CSW UI → API Keys)
    CSW_API_SECRET - API secret (hex string from CSW UI → API Keys)

Optional:
    CSW_VERIFY_SSL - Set to "false" to skip TLS verification (corporate proxies)
                     Default: "true"
"""

import base64
import hashlib
import hmac
import json
import os
import random
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


def _load_dotenv():
    """Load KEY=value pairs from .env file next to this script.
    Does not override variables already set in the environment.
    """
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.isfile(env_path):
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            if "=" not in line:
                continue
            # partition splits only on the first '=', so values may contain '=' (e.g. base64).
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, val)


def get_config():
    """Read and validate required environment variables."""
    url    = os.environ.get("CSW_API_URL", "").rstrip("/")
    key    = os.environ.get("CSW_API_KEY", "")
    secret = os.environ.get("CSW_API_SECRET", "")

    missing = [v for v, val in [("CSW_API_URL", url), ("CSW_API_KEY", key), ("CSW_API_SECRET", secret)] if not val]
    if missing:
        print(json.dumps({
            "error": f"Missing environment variables: {', '.join(missing)}",
            "hint":  "Copy .env.example to .env and fill in your cluster credentials."
        }), file=sys.stderr)
        sys.exit(1)

    verify_ssl = os.environ.get("CSW_VERIFY_SSL", "true").lower() != "false"
    return url, key, secret, verify_ssl


def compute_signature(secret, method, path, checksum, content_type, timestamp):
    """Compute HMAC-SHA256 signature per the CSW OpenAPI authentication specification.

    Canonical message format:
        METHOD\\nPATH\\nCHECKSUM\\nCONTENT-TYPE\\nTIMESTAMP\\n
    """
    msg = "\n".join([method, path, checksum, content_type, timestamp]) + "\n"
    sig = hmac.new(secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256)
    # CSW expects the raw HMAC-SHA256 digest, Base64-encoded, as the Authorization value (not a scheme prefix).
    return base64.b64encode(sig.digest()).decode("utf-8")


# 429 is the rate-limit response. 503 is the overload response clusters
# return when the same key is calling too fast. GET and read-only search
# POST are safe to repeat. PUT and DELETE are not retried.
_THROTTLE_STATUS = (429, 503)
_RETRY_METHODS = ("GET", "POST")
_DEFAULT_ATTEMPTS = 5
_DEFAULT_MAX_SLEEP = 8.0


def _retry_budget():
    """How many tries, and the longest pause between them.

    CSW_RETRY_ATTEMPTS includes the first call (1–8). CSW_RETRY_MAX_SLEEP
    caps a single wait, including a Retry-After value, so one tool call
    cannot sit for minutes.
    """
    try:
        attempts = int(os.environ.get("CSW_RETRY_ATTEMPTS", _DEFAULT_ATTEMPTS))
    except ValueError:
        attempts = _DEFAULT_ATTEMPTS
    try:
        max_sleep = float(os.environ.get("CSW_RETRY_MAX_SLEEP", _DEFAULT_MAX_SLEEP))
    except ValueError:
        max_sleep = _DEFAULT_MAX_SLEEP
    return max(1, min(8, attempts)), max(0.0, min(30.0, max_sleep))


def _retry_after_seconds(headers):
    """Seconds from a Retry-After header, or None when it is missing or unreadable."""
    if headers is None:
        return None
    raw = headers.get("Retry-After")
    if not raw:
        return None
    raw = str(raw).strip()
    try:
        return max(0.0, float(raw))
    except ValueError:
        pass
    try:
        when = parsedate_to_datetime(raw)
    except (TypeError, ValueError, IndexError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return max(0.0, (when - datetime.now(timezone.utc)).total_seconds())


def _pause_for_throttle(attempt, headers, max_sleep):
    """Wait for Retry-After, otherwise back off 0.5s, 1s, 2s, 4s, …"""
    wait = _retry_after_seconds(headers)
    if wait is None:
        wait = 0.5 * (2 ** attempt)
    wait = min(max_sleep, wait)
    # A short jitter keeps several tools from retrying on the same instant.
    wait += random.uniform(0, 0.25)
    time.sleep(wait)


def make_request(method, path, body=None, params=None):
    """
    Execute an authenticated CSW API request and return a parsed result dict.

    HMAC-SHA256 authentication flow:
      1. Build canonical request line (METHOD\\nPATH\\nCHECKSUM\\nCONTENT_TYPE\\nTIMESTAMP\\n)
      2. Compute HMAC-SHA256(secret, canonical_request), base64 encode the digest
      3. Send the signature in the Authorization header along with the API key (Id header)
         and the same timestamp used to sign

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        path:   API path starting with /openapi/v1/...
        body:   Optional request body (dict, list, or JSON string)
        params: Optional dict of query parameters — appended to path BEFORE signing

    Returns:
        dict with keys:
          - status: HTTP status code (0 if connection failed)
          - data:   parsed JSON response or raw text
          - error:  (only on failure) error description
          - retries: how many extra attempts ran (only when greater than zero)

    GET and POST are tried again when the cluster answers 429 or 503.
    Each attempt is signed again, because the timestamp is part of the
    signature. The pause follows Retry-After when the cluster sends one,
    otherwise it doubles from half a second and stays under the cap.
    """
    base_url, api_key, api_secret, verify_ssl = get_config()
    method = method.upper()

    # Query parameters must be appended before signing — signature covers the full path
    if params:
        path = f"{path}?{urllib.parse.urlencode(params)}"

    url          = f"{base_url}{path}"
    content_type = "application/json"

    # Normalize body to bytes for signing and transmission
    body_bytes = b""
    if body:
        if isinstance(body, str):
            body_bytes = body.encode("utf-8")
        elif isinstance(body, (dict, list)):
            body_bytes = json.dumps(body).encode("utf-8")

    # Body checksum is only included for POST/PUT with a non-empty body.
    # For GET/DELETE and empty POST/PUT, checksum must be the empty string.
    checksum = hashlib.sha256(body_bytes).hexdigest() if method in ("POST", "PUT") and body_bytes else ""

    # SSL context — bypass verification if requested (for corporate TLS proxies)
    if not verify_ssl:
        import ssl
        ctx = ssl.create_default_context()
        # INSECURE: only use when corporate TLS inspection breaks cert validation.
        # Proper fix: install the corporate root CA in the system trust store.
        ctx.check_hostname = False
        ctx.verify_mode    = ssl.CERT_NONE
    else:
        ctx = None

    attempts, max_sleep = _retry_budget()
    retriable = method in _RETRY_METHODS
    last = None
    for attempt in range(attempts):
        # CSW expects ISO 8601 timestamp in UTC with explicit +0000 offset.
        # A retry must use a new timestamp, or the signature will not match.
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0000")
        signature = compute_signature(api_secret, method, path, checksum, content_type, timestamp)
        headers = {
            "Content-Type":  content_type,
            "Id":            api_key,       # API key identifier
            "Authorization": signature,     # HMAC-SHA256 signature (base64)
            "Timestamp":     timestamp,     # Must match the timestamp used in signature
            "User-Agent":    "csw-tme-toolkit/1.0",
        }
        if checksum:
            headers["X-Tetration-Cksum"] = checksum

        req = urllib.request.Request(
            url,
            data=body_bytes if body_bytes else None,
            headers=headers,
            method=method,
        )
        try:
            kwargs = {"context": ctx} if ctx else {}
            with urllib.request.urlopen(req, **kwargs) as resp:
                raw = resp.read().decode("utf-8")
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    data = raw
                result = {"status": resp.status, "data": data}
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace")
            try:
                err_data = json.loads(raw)
            except json.JSONDecodeError:
                err_data = raw
            result = {"status": e.code, "error": str(e.reason), "data": err_data}
            if retriable and e.code in _THROTTLE_STATUS and attempt + 1 < attempts:
                _pause_for_throttle(attempt, e.headers, max_sleep)
                last = result
                continue
            if attempt:
                result["retries"] = attempt
            return result
        except urllib.error.URLError as e:
            return {"status": 0, "error": f"Connection failed: {e.reason}", "data": None}

        if attempt:
            result["retries"] = attempt
        return result

    if last is not None and attempts > 1:
        last["retries"] = attempts - 1
    return last or {"status": 0, "error": "Request was not sent", "data": None}


def main():
    """Parse CLI arguments, optional --limit/--offset and generic --key value pairs, then run one signed request."""
    _load_dotenv()
    if len(sys.argv) < 3:
        print("Usage: csw_api.py METHOD PATH [BODY_JSON] [--limit N] [--offset N]")
        print()
        print("Examples:")
        print("  csw_api.py GET /openapi/v1/app_scopes")
        print("  csw_api.py GET /openapi/v1/sensors")
        print("  csw_api.py GET /openapi/v1/applications")
        print('  csw_api.py POST /openapi/v1/inventory/search \'{"filter": {"type": "eq", "field": "os", "value": "windows"}}\'')
        print("  csw_api.py GET /openapi/v1/sensors --limit 50 --offset 0")
        sys.exit(1)

    method = sys.argv[1].upper()
    path   = sys.argv[2]
    body   = None
    params = {}
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == "--limit" and i + 1 < len(sys.argv):
            params["limit"] = sys.argv[i + 1]; i += 2
        elif sys.argv[i] == "--offset" and i + 1 < len(sys.argv):
            params["offset"] = sys.argv[i + 1]; i += 2
        elif sys.argv[i].startswith("--"):
            k = sys.argv[i].lstrip("-")
            if i + 1 < len(sys.argv):
                params[k] = sys.argv[i + 1]; i += 2
            else:
                i += 1
        elif body is None:
            try:
                body = json.loads(sys.argv[i])
            except json.JSONDecodeError:
                print(json.dumps({"error": f"Invalid JSON body: {sys.argv[i]}"}))
                sys.exit(1)
            i += 1
        else:
            i += 1

    result = make_request(method, path, body=body, params=params if params else None)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
