"""Optional real provider verification; subprocess prevents secret-rich pytest tracebacks."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from keycloak_harness import CALLBACK, ProbeFailure, callback_code, challenge


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
