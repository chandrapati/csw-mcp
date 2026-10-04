#!/usr/bin/env python3
"""Retry behavior for a busy read. No cluster and no real credentials."""

from __future__ import annotations

import io
import os
import sys
import unittest
import urllib.error
from email.message import Message
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

os.environ.setdefault("CSW_API_URL", "https://example.invalid")
os.environ.setdefault("CSW_API_KEY", "test-key")
os.environ.setdefault("CSW_API_SECRET", "test-secret")
os.environ["CSW_RETRY_ATTEMPTS"] = "3"
os.environ["CSW_RETRY_MAX_SLEEP"] = "8"

from csw_mcp.vendor import csw_api  # noqa: E402


def _http_error(code, body=b"{}", retry_after=None):
    headers = Message()
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    return urllib.error.HTTPError(
        "https://example.invalid/openapi/v1/sensors",
        code,
        "busy",
        headers,
        io.BytesIO(body),
    )


class _Ok:
    status = 200

    def read(self):
        return b'[{"ok": true}]'

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class RetryTests(unittest.TestCase):
    def test_busy_read_is_tried_again_and_then_succeeds(self):
        calls = {"n": 0}

        def urlopen(req, **kwargs):
            calls["n"] += 1
            if calls["n"] < 3:
                raise _http_error(429, retry_after="0")
            return _Ok()

        with mock.patch.object(csw_api.urllib.request, "urlopen", urlopen):
            with mock.patch.object(csw_api.time, "sleep") as slept:
                result = csw_api.make_request("GET", "/openapi/v1/sensors")

        self.assertEqual(result["status"], 200)
        self.assertEqual(result["retries"], 2)
        self.assertEqual(calls["n"], 3)
        self.assertEqual(slept.call_count, 2)

    def test_a_write_is_not_retried(self):
        calls = {"n": 0}

        def urlopen(req, **kwargs):
            calls["n"] += 1
            raise _http_error(429, retry_after="0")

        with mock.patch.object(csw_api.urllib.request, "urlopen", urlopen):
            with mock.patch.object(csw_api.time, "sleep") as slept:
                result = csw_api.make_request("DELETE", "/openapi/v1/sensors/x")

        self.assertEqual(result["status"], 429)
        self.assertEqual(calls["n"], 1)
        self.assertEqual(slept.call_count, 0)
        self.assertNotIn("retries", result)

    def test_gives_up_after_the_attempt_budget(self):
        def urlopen(req, **kwargs):
            raise _http_error(503, body=b'{"error":"later"}', retry_after="0")

        with mock.patch.object(csw_api.urllib.request, "urlopen", urlopen):
            with mock.patch.object(csw_api.time, "sleep"):
                result = csw_api.make_request("GET", "/openapi/v1/app_scopes")

        self.assertEqual(result["status"], 503)
        self.assertEqual(result["retries"], 2)
        self.assertEqual(result["data"], {"error": "later"})


if __name__ == "__main__":
    unittest.main()
