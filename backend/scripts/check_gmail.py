import _bootstrap  # noqa: F401
from app.core.config import get_settings
from app.services.factory import build_gmail


def main():
    settings = get_settings()

    if settings.gmail_mode != "live":
        raise SystemExit(
            "Set GMAIL_MODE=live in backend/.env first."
        )

    print("Authenticating with Gmail...")
    gmail = build_gmail()

    profile = gmail.profile()
    print("Authentication: OK")
    print(f"Mailbox: {profile.get('emailAddress')}")

    messages = gmail.list_messages(limit=5)
    print(f"Unread inbox messages returned: {len(messages)}")

    for message in messages:
        preview = " ".join(
            message.body.split()
        )[:80]
        print(
            f"- {message.sender_email} | "
            f"{message.subject} | "
            f"{preview}"
        )


if __name__ == "__main__":
    main()
