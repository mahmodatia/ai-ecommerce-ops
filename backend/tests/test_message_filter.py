from app.domain.models import CustomerMessage
from app.services.message_filter import (
    clean_message_text,
    is_support_candidate,
)


def message(subject, body):
    return CustomerMessage(
        id="x",
        sender_email="customer@example.com",
        subject=subject,
        body=body,
    )


def test_support_email_with_order_is_candidate():
    assert is_support_candidate(
        message(
            "Where is my order #1001?",
            "I have not received tracking yet.",
        )
    )


def test_newsletter_is_not_candidate():
    assert not is_support_candidate(
        message(
            "Welcome to our product",
            "Read our latest news and download the app.",
        )
    )


def test_clear_refund_without_order_can_still_be_candidate():
    assert is_support_candidate(
        message(
            "Refund request",
            "I want a return and refund please.",
        )
    )


def test_clean_message_removes_quoted_reply_and_long_links():
    text = (
        "Please refund order #1001.\n"
        "On Monday Customer wrote:\n"
        + "https://example.com/"
        + ("x" * 500)
    )

    cleaned = clean_message_text(text)
    assert "Please refund order #1001." in cleaned
    assert "On Monday" not in cleaned
