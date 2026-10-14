"""Opt-in M04 verification using owned, disposable containers; never existing databases."""

import argparse
import json
import os
import re
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--isolated", action="store_true", required=True)
    parser.add_argument("--keycloak", action="store_true")
    parser.add_argument("--browser", action="store_true")
    args = parser.parse_args()
    # Explicitly discard ambient application/test configuration, including proxy URLs.
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(
            ("TEST_", "WEB_", "OIDC_", "KEYCLOAK_", "DATABASE_", "CORS_", "API_INTERNAL_")
        )
        and k.upper() not in {"HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"}
    }
    env.update(APP_ENV="test", OIDC_ENABLED="false", CORS_ORIGINS="[]", TEST_WEB_ISOLATED="1")
    name = "libris-m0409-" + secrets.token_hex(8)
    containers: list[str] = []
    api: subprocess.Popen[bytes] | None = None
    evidence = Path(tempfile.mkdtemp(prefix=name + "-"))
    print(f"Private local evidence: {evidence}", flush=True)
    python = str(ROOT / "apps/api/.venv/bin/python")

    def command(stage: str, argv: list[str], cwd: Path = ROOT) -> str:
        result = subprocess.run(
            argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=600, check=False
        )
        log = evidence / (stage + ".log")
        log.write_text(result.stdout + result.stderr)
        log.chmod(0o600)
        if result.returncode:
            raise RuntimeError(f"{stage}: exit {result.returncode}; inspect private log")
        if stage in {"api-integration", "web-store", "web-http", "web-keycloak"} and (
            re.search(r"\b[1-9]\d* skipped\b", result.stdout)
            or re.search(r"[ℹ#] skipped [1-9]\d*", result.stdout)
        ):
            raise RuntimeError(f"{stage}: unexpected skips; integration not approved")
        print(f"PASS {stage}", flush=True)
        for line in result.stdout.splitlines():
            if re.fullmatch(r"[= ]*\d+ passed.* in [\d.]+s[= ]*", line) or re.match(
                r"[ℹ#] (tests|pass|fail|skipped|cancelled) \d+$", line
            ):
                print(line, flush=True)
        return result.stdout.strip()

    def ready(url: str) -> None:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for _ in range(180):
            try:
                with opener.open(url, timeout=1) as response:
                    if response.status == 200:
                        return
            except (OSError, urllib.error.URLError):
                time.sleep(0.5)
        raise RuntimeError("Local service readiness timeout")

    try:
        command("docker-access", ["docker", "info", "--format", "{{.ServerVersion}}"])
        env["POSTGRES_PASSWORD"] = secrets.token_urlsafe(32)
        pg = name + "-pg"
        pg_port = free_port()
        command(
            "postgres-create",
            [
                "docker",
                "run",
                "--pull=never",
                "--detach",
                "--rm",
                "--name",
                pg,
                "--label",
                f"libris.verification={name}",
                "--publish",
                f"127.0.0.1:{pg_port}:5432",
                "--tmpfs",
                "/var/lib/postgresql/data",
                "--env",
                "POSTGRES_PASSWORD",
                "postgres:17-bookworm",
            ],
        )
        containers.append(pg)
        for _ in range(100):
            probe = subprocess.run(
                ["docker", "exec", pg, "pg_isready", "-U", "postgres"],
                capture_output=True,
                check=False,
            )
            if probe.returncode == 0:
                break
            time.sleep(0.2)
        else:
            raise RuntimeError("Disposable PostgreSQL unavailable")
        databases = {
            "TEST_DATABASE_URL": "semantic",
            "TEST_MIGRATION_DATABASE_URL": "audit_migration",
            "TEST_EDITORIAL_MIGRATION_DATABASE_URL": "editorial_migration",
            "TEST_WEB_MIGRATION_DATABASE_URL": "web_migration",
            "TEST_WEB_DATABASE_URL": "web_store",
            "TEST_WEB_HTTP_DATABASE_URL": "web_http",
            "TEST_ADMIN_API_DATABASE_URL": "web_admin",
            "TEST_KEYCLOAK_WEB_DATABASE_URL": "web_keycloak",
        }
        for variable, database in databases.items():
            command(
                "create-" + database, ["docker", "exec", pg, "createdb", "-U", "postgres", database]
            )
            scheme = (
                "postgresql+asyncpg"
                if variable
                in {
                    "TEST_DATABASE_URL",
                    "TEST_MIGRATION_DATABASE_URL",
                    "TEST_EDITORIAL_MIGRATION_DATABASE_URL",
                    "TEST_WEB_MIGRATION_DATABASE_URL",
                }
                else "postgresql"
            )
            env[variable] = (
                f"{scheme}://postgres:{env['POSTGRES_PASSWORD']}@127.0.0.1:{pg_port}/{database}"
            )
        env["DATABASE_URL"] = env["TEST_DATABASE_URL"]
        command("alembic", [python, "-m", "alembic", "upgrade", "head"], ROOT / "apps/api")
        if args.keycloak:
            kc_port, api_port, web_port = free_port(), free_port(), free_port()
            issuer = f"http://127.0.0.1:{kc_port}/realms/libris"
            origin = f"http://127.0.0.1:{web_port}"
            realm = json.loads((ROOT / "infrastructure/keycloak/libris-realm.json").read_text())
            for client in realm["clients"]:
                if client["clientId"] == "libris-web":
                    client["redirectUris"].append(origin + "/oidc/callback")
                    client["webOrigins"].append(origin)
                    client["attributes"]["post.logout.redirect.uris"] += (
                        f"##{origin}/pt##{origin}/en"
                    )
            # Public realm configuration contains no accounts or credentials.
            with tempfile.TemporaryDirectory(prefix=name + "-realm-") as directory:
                Path(directory).chmod(0o755)
                realm_file = Path(directory) / "libris-realm.json"
                realm_file.write_text(json.dumps(realm))
                realm_file.chmod(0o644)
                env.update(
                    KC_BOOTSTRAP_ADMIN_USERNAME="m0409-admin",
                    KC_BOOTSTRAP_ADMIN_PASSWORD=secrets.token_urlsafe(32),
                )
                kc = name + "-kc"
                command(
                    "keycloak-create",
                    [
                        "docker",
                        "run",
                        "--pull=never",
                        "--detach",
                        "--rm",
                        "--name",
                        kc,
                        "--label",
                        f"libris.verification={name}",
                        "--publish",
                        f"127.0.0.1:{kc_port}:8080",
                        "--tmpfs",
                        "/opt/keycloak/data:uid=1000,gid=0",
                        "--volume",
                        f"{directory}:/opt/keycloak/data/import:ro",
                        "--env",
                        "KC_BOOTSTRAP_ADMIN_USERNAME",
                        "--env",
                        "KC_BOOTSTRAP_ADMIN_PASSWORD",
                        "quay.io/keycloak/keycloak:26.8.0",
                        "start-dev",
                        "--import-realm",
                        "--hostname",
                        issuer.removesuffix("/realms/libris"),
                    ],
                )
                containers.append(kc)
                env["TEST_KEYCLOAK_CONTAINER"] = kc
                ready(issuer + "/.well-known/openid-configuration")
            env.update(
                TEST_KEYCLOAK_ENABLED="1",
                TEST_KEYCLOAK_ISOLATED="1",
                TEST_KEYCLOAK_GOVERNANCE="1",
                TEST_KEYCLOAK_ISSUER=issuer,
                KEYCLOAK_ADMIN_USERNAME=env["KC_BOOTSTRAP_ADMIN_USERNAME"],
                KEYCLOAK_ADMIN_PASSWORD=env["KC_BOOTSTRAP_ADMIN_PASSWORD"],
                TEST_KEYCLOAK_API_URL=f"http://127.0.0.1:{api_port}",
                TEST_KEYCLOAK_WEB_ENABLED="1",
                TEST_KEYCLOAK_WEB_ISSUER=issuer,
                TEST_KEYCLOAK_WEB_ORIGIN=origin,
                TEST_KEYCLOAK_ADMIN_USERNAME=env["KC_BOOTSTRAP_ADMIN_USERNAME"],
                TEST_KEYCLOAK_ADMIN_PASSWORD=env["KC_BOOTSTRAP_ADMIN_PASSWORD"],
            )
            api_env = env | {
                "APP_ENV": "development",
                "OIDC_ENABLED": "true",
                "OIDC_ISSUER_URL": issuer,
            }
            with (evidence / "api.log").open("wb") as output:
                api = subprocess.Popen(
                    [
                        python,
                        "-m",
                        "uvicorn",
                        "libris.main:app",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(api_port),
                        "--no-access-log",
                    ],
                    cwd=ROOT / "apps/api",
                    env=api_env,
                    stdout=output,
                    stderr=output,
                )
            (evidence / "api.log").chmod(0o600)
            ready(env["TEST_KEYCLOAK_API_URL"] + "/health")
        integration = [python, "-m", "pytest", "-c", "pyproject.toml", "../../tests/integration"]
        if not args.keycloak:
            integration.extend(["-m", "not keycloak"])
        command(
            "api-integration",
            integration,
            ROOT / "apps/api",
        )
        command("web-store", ["npm", "run", "test:integration"], ROOT / "apps/web")
        if args.browser:
            env["TEST_WEB_BROWSER_ENABLED"] = "1"
        command("web-http", ["npm", "run", "test:http"], ROOT / "apps/web")
        if args.keycloak:
            command("web-keycloak", ["npm", "run", "test:keycloak"], ROOT / "apps/web")
        return 0
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        # Exceptions/commands can contain credentials. Publish only fixed stage messages.
        print(
            str(error)
            if isinstance(error, RuntimeError)
            else "FAIL: local command unavailable or timed out",
            flush=True,
        )
        return 1
    finally:
        if api is not None:
            api.terminate()
            try:
                api.wait(timeout=10)
            except subprocess.TimeoutExpired:
                api.kill()
                api.wait(timeout=10)
        cleanup_failed = False
        for container in reversed(containers):
            result = subprocess.run(
                ["docker", "stop", "--time", "10", container], capture_output=True, check=False
            )
            outcome = "PASS" if result.returncode == 0 else "FAILED"
            print(f"Owned container cleanup {outcome}: {container}", flush=True)
            if result.returncode != 0:
                cleanup_failed = True
        if cleanup_failed:
            raise RuntimeError("Owned container cleanup failed; inspect test resources")


if __name__ == "__main__":
    sys.exit(main())
