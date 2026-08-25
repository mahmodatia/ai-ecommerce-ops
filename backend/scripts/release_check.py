from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN_FILES = {
    ROOT / "backend" / ".env",
    ROOT / "backend" / "credentials.json",
    ROOT / "backend" / "token.json",
    ROOT / "backend" / "dev.db",
    ROOT / "backend" / "test.db",
}

FORBIDDEN_UI_PHRASES = [
    "Approve & Send",
    "Execute Operational Change",
    "approved automatically by AI",
    "AI Handled",
    "processed a full refund",
    "I have gone ahead and processed",
    "Refund processed automatically",
    "Issue Refund",
    "Update Fulfillment",
    "Sentiment Analysis",
    "Carrier API",
    "discount code",
    "return label",
    "VIP Tier",
    "Store Credit",
    "+ New Automation",
    "+ New Workflow",
]

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
ALLOWED_PUBLIC_EMAIL_DOMAINS = {"example.com"}

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]

TEXT_SUFFIXES = {
    ".py", ".js", ".html", ".css", ".md", ".txt", ".yml", ".yaml", ".toml", ".json"
}


def main():
    errors: list[str] = []

    for path in FORBIDDEN_FILES:
        if path.exists():
            errors.append(
                f"Secret/runtime file must not be packaged: {path.relative_to(ROOT)}"
            )

    logo = ROOT / "frontend" / "assets" / "logo.svg"
    brand_config = ROOT / "frontend" / "js" / "brand.js"
    if not logo.exists():
        errors.append("Missing replaceable frontend/assets/logo.svg branding slot")
    if not brand_config.exists():
        errors.append("Missing frontend/js/brand.js branding configuration")

    frontend_files = list((ROOT / "frontend").rglob("*.html")) + list(
        (ROOT / "frontend").rglob("*.js")
    )
    for path in frontend_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for phrase in FORBIDDEN_UI_PHRASES:
            if phrase.lower() in text.lower():
                errors.append(
                    f"Unsafe/out-of-scope UI phrase '{phrase}' in "
                    f"{path.relative_to(ROOT)}"
                )

    # Scan project text for obvious live API keys and accidental real email
    # addresses. Mock/test identities use example.com.
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in {".venv", "__pycache__", ".pytest_cache"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"Possible live API key in {path.relative_to(ROOT)}")
        for match in EMAIL_PATTERN.finditer(text):
            domain = match.group(1).lower()
            if domain not in ALLOWED_PUBLIC_EMAIL_DOMAINS:
                errors.append(
                    f"Possible real email/PII in {path.relative_to(ROOT)}: {match.group(0)}"
                )

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        lower_name = path.name.lower()
        if lower_name in {"credentials.json", "token.json"}:
            errors.append(f"OAuth file must not be packaged: {path.relative_to(ROOT)}")
        if path.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
            errors.append(f"Runtime database must not be packaged: {path.relative_to(ROOT)}")
        if lower_name == ".env":
            errors.append(f"Environment secret file must not be packaged: {path.relative_to(ROOT)}")

    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    if "ALLOW_LIVE_ACTIONS=false" not in env_example:
        errors.append(".env.example must keep ALLOW_LIVE_ACTIONS=false")
    if "GMAIL_MANUAL_SEND_ENABLED=false" not in env_example:
        errors.append(".env.example must keep GMAIL_MANUAL_SEND_ENABLED=false")

    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    if "APP_ENV: ${APP_ENV:-development}" not in compose:
        errors.append("Docker Compose must pass APP_ENV into application services")
    if '"5432:5432"' in compose or '"6379:6379"' in compose:
        errors.append("PostgreSQL/Redis must not be exposed on host ports by default")

    pyproject = (ROOT / "backend" / "pyproject.toml").read_text(encoding="utf-8")
    if 'version = "3.0.0"' not in pyproject:
        errors.append("Backend package version must be final 3.0.0")

    if errors:
        print("Release check FAILED")
        for error in errors:
            print("-", error)
        raise SystemExit(1)

    print("Release check PASSED")
    print("- no packaged OAuth/API secret/runtime files or non-example email addresses")
    print("- no forbidden auto-execution/out-of-scope UI phrases")
    print("- final logo slot and brand config present")
    print("- hard safety boundary remains disabled")
    print("- final package version is 3.0.0")


if __name__ == "__main__":
    main()
