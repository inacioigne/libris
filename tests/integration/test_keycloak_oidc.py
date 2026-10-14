"""Optional real provider verification; subprocess prevents secret-rich pytest tracebacks."""

import os
import subprocess
import sys
from pathlib import Path

import httpx
import pytest
from keycloak_harness import (
    CALLBACK,
    ProbeFailure,
    callback_code,
    challenge,
    loopback_probe_cookies,
)


def test_pkce_rfc7636_vector() -> None:
    assert challenge("dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk") == (
        "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
    )


@pytest.mark.parametrize(
    "location",
    [
        CALLBACK + "?code=test&state=wrong",
        CALLBACK + "?code=test&state=expected&state=expected",
        CALLBACK + "?code=test&code=other&state=expected",
        "http://example.invalid/callback?code=test&state=expected",
        CALLBACK + "?error=denied&state=expected",
    ],
)
def test_callback_rejects_tampering(location: str) -> None:
    with pytest.raises(ProbeFailure):
        callback_code(location, "expected")


def test_callback_accepts_matching_state() -> None:
    assert callback_code(CALLBACK + "?code=test&state=expected", "expected") == "test"


@pytest.mark.parametrize(
    "issuer,isolated,adapted",
    [
        ("http://127.0.0.1:8080/realms/libris", "1", True),
        ("http://keycloak.localhost:8080/realms/libris", "1", True),
        ("http://127.0.0.1:8080/realms/libris", "0", False),
        ("https://127.0.0.1:8080/realms/libris", "1", False),
        ("http://example.invalid:8080/realms/libris", "1", False),
    ],
)
def test_probe_cookie_exception_is_local_and_opt_in(
    issuer: str, isolated: str, adapted: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    from http.cookiejar import Cookie
    from urllib.parse import urlsplit

    monkeypatch.setenv("TEST_KEYCLOAK_ISOLATED", isolated)
    host = urlsplit(issuer).hostname
    assert host is not None
    with httpx.Client() as browser:
        for domain, path in [
            (host, "/realms/libris/"),
            (host, "/other/"),
            ("other.invalid", "/realms/libris/"),
        ]:
            browser.cookies.jar.set_cookie(
                Cookie(
                    0,
                    "probe",
                    "synthetic",
                    None,
                    False,
                    domain,
                    True,
                    False,
                    path,
                    True,
                    True,
                    None,
                    True,
                    None,
                    None,
                    {},
                )
            )
        loopback_probe_cookies(browser, issuer)
        cookies = list(browser.cookies.jar)
        assert cookies[0].secure is not adapted
        assert all(cookie.secure for cookie in cookies[1:])


@pytest.mark.keycloak
def test_real_keycloak_code_pkce_and_resource_server() -> None:
    if os.environ.get("TEST_KEYCLOAK_ENABLED") != "1":
        pytest.skip("real Keycloak requires TEST_KEYCLOAK_ENABLED=1 and isolated configuration")
    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("keycloak_harness.py"))],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    # The harness emits only fixed, sanitized evidence. Never echo stderr or environment.
    assert result.returncode == 0, result.stdout
    print(result.stdout, end="")


@pytest.mark.keycloak
def test_real_keycloak_governance() -> None:
    if os.environ.get("TEST_KEYCLOAK_GOVERNANCE") != "1":
        pytest.skip("governance requires a newly created disposable Keycloak")
    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("keycloak_governance_harness.py"))],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    print(result.stdout, end="")
