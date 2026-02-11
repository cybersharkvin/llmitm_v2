"""Tests for HTTP traffic fingerprinting."""

import pytest

from llmitm_v2.fingerprinter import Fingerprinter


@pytest.fixture
def fingerprinter():
    return Fingerprinter()


@pytest.fixture
def express_traffic():
    return """>>> GET / HTTP/1.1
Host: localhost:3000

<<< HTTP/1.1 200 OK
X-Powered-By: Express
Access-Control-Allow-Origin: *

<!DOCTYPE html>"""


@pytest.fixture
def jwt_traffic():
    return """>>> POST /rest/user/login HTTP/1.1
Host: localhost:3000

{"email":"admin@juice-sh.op","password":"admin123"}

<<< HTTP/1.1 200 OK
X-Powered-By: Express

{"authentication":{"token":"eyJ..."}}

>>> GET /rest/user/whoami HTTP/1.1
Host: localhost:3000
Authorization: Bearer eyJ...

<<< HTTP/1.1 200 OK
X-Powered-By: Express

{"user":{"id":1}}"""


@pytest.fixture
def api_traffic():
    return """>>> GET /api/Products HTTP/1.1
Host: localhost:3000

<<< HTTP/1.1 200 OK
X-Powered-By: Express

{"data":[]}

>>> GET /api/Users/1 HTTP/1.1
Host: localhost:3000

<<< HTTP/1.1 200 OK
X-Powered-By: Express

{"data":{"id":1}}

>>> GET /rest/health HTTP/1.1
Host: localhost:3000

<<< HTTP/1.1 200 OK
X-Powered-By: Express

{"status":"ok"}"""


def test_fingerprint_extracts_express_tech_stack(fingerprinter, express_traffic):
    fp = fingerprinter.fingerprint(express_traffic)
    assert fp.tech_stack == "Express"


def test_fingerprint_extracts_jwt_auth(fingerprinter, jwt_traffic):
    fp = fingerprinter.fingerprint(jwt_traffic)
    assert fp.auth_model == "JWT Bearer"


def test_fingerprint_extracts_endpoint_pattern(fingerprinter, api_traffic):
    fp = fingerprinter.fingerprint(api_traffic)
    assert fp.endpoint_pattern in ["/api/*", "/rest/*"]


def test_fingerprint_extracts_cors_signal(fingerprinter, express_traffic):
    fp = fingerprinter.fingerprint(express_traffic)
    assert "CORS permissive" in fp.security_signals


def test_fingerprint_unknown_when_no_headers(fingerprinter):
    traffic = """>>> GET / HTTP/1.1
Host: localhost:3000

<<< HTTP/1.1 200 OK
Content-Type: text/html

<html></html>"""
    fp = fingerprinter.fingerprint(traffic)
    assert fp.tech_stack == "Unknown"
    assert fp.auth_model == "Unknown"


def test_parse_traffic_log_format(fingerprinter):
    traffic = """>>> GET /api/test HTTP/1.1
Host: example.com

<<< HTTP/1.1 200 OK
Content-Type: application/json

{"result":"ok"}"""
    requests, responses = fingerprinter._parse_traffic_log(traffic)
    assert len(requests) == 1
    assert len(responses) == 1
    assert requests[0]["method"] == "GET"
    assert requests[0]["path"] == "/api/test"
    assert responses[0]["status_code"] == 200
