from __future__ import annotations

import base64
import html
import os
import re
from email.message import EmailMessage
from email.utils import parseaddr

from app.core.errors import IntegrationError
from app.domain.models import CustomerMessage
from app.services.message_filter import (
    clean_message_text,
    is_support_candidate,
)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
]


class GmailClient:
    def __init__(
        self,
        credentials_file: str,
        token_file: str,
        query: str = "in:inbox is:unread",
        *,
        retries: int = 3,
        support_only: bool = True,
        max_body_chars: int = 5000,
    ):
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        self.credentials_file = credentials_file
        self.token_file = token_file
        self.query = query
        self.retries = max(0, retries)
        self.support_only = support_only
        self.max_body_chars = max_body_chars

        creds = None

        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(
                token_file,
                SCOPES,
            )

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_file):
                    raise FileNotFoundError(
                        f"Gmail OAuth credentials file not found: "
                        f"{credentials_file}"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file,
                    SCOPES,
                )
                creds = flow.run_local_server(
                    port=0,
                    prompt="consent",
                )

            with open(token_file, "w", encoding="utf-8") as f:
                f.write(creds.to_json())

        self.service = build(
            "gmail",
            "v1",
            credentials=creds,
            cache_discovery=False,
        )

    def _execute(self, request, operation: str):
        try:
            return request.execute(num_retries=self.retries)
        except Exception as exc:
            raise IntegrationError(
                "gmail",
                f"Gmail {operation} failed: {type(exc).__name__}",
            ) from exc

    def profile(self) -> dict:
        return self._execute(
            self.service.users().getProfile(userId="me"),
            "profile lookup",
        )

    def list_messages(
        self,
        limit: int = 10,
        query: str | None = None,
        support_only: bool | None = None,
    ) -> list[CustomerMessage]:
        result = self._execute(
            self.service.users().messages().list(
                userId="me",
                q=query or self.query,
                maxResults=max(1, min(limit * 3, 75)),
            ),
            "message list",
        )

        refs = result.get("messages", [])
        messages = []
        only_support = (
            self.support_only
            if support_only is None
            else support_only
        )

        for item in refs:
            parsed = self.get_message(item["id"])
            if not parsed:
                continue
            if only_support and not is_support_candidate(parsed):
                continue
            messages.append(parsed)
            if len(messages) >= limit:
                break

        return messages

    def get_message(
        self,
        message_id: str,
    ) -> CustomerMessage | None:
        raw = self._execute(
            self.service.users().messages().get(
                userId="me",
                id=message_id,
                format="full",
            ),
            "message read",
        )

        payload = raw.get("payload", {})
        headers = self._headers(payload)
        sender_email = parseaddr(
            headers.get("from", "")
        )[1]

        body = clean_message_text(
            self._extract_text(payload),
            max_chars=self.max_body_chars,
        )

        return CustomerMessage(
            id=raw["id"],
            sender_email=sender_email,
            subject=headers.get("subject") or "(no subject)",
            body=body,
        )

    def create_reply_draft(
        self,
        original_message_id: str,
        to_email: str,
        subject: str,
        body: str,
    ) -> dict:
        original = self._execute(
            self.service.users().messages().get(
                userId="me",
                id=original_message_id,
                format="metadata",
                metadataHeaders=[
                    "Message-ID",
                    "References",
                    "Subject",
                ],
            ),
            "thread metadata lookup",
        )

        headers = self._headers(
            original.get("payload", {})
        )

        message = EmailMessage()
        message["To"] = to_email
        message["Subject"] = (
            subject
            if subject.lower().startswith("re:")
            else f"Re: {subject}"
        )

        original_message_id_header = headers.get("message-id")
        references = headers.get("references", "")

        if original_message_id_header:
            message["In-Reply-To"] = original_message_id_header
            message["References"] = (
                f"{references} {original_message_id_header}".strip()
            )

        message.set_content(body)

        raw = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode("ascii")

        request_body = {
            "message": {
                "raw": raw,
                "threadId": original.get("threadId"),
            }
        }

        return self._execute(
            self.service.users().drafts().create(
                userId="me",
                body=request_body,
            ),
            "draft creation",
        )

    def send_draft(self, draft_id: str) -> dict:
        return self._execute(
            self.service.users().drafts().send(
                userId="me",
                body={"id": draft_id},
            ),
            "draft sending",
        )

    @staticmethod
    def _headers(payload: dict) -> dict[str, str]:
        return {
            item.get("name", "").lower(): item.get("value", "")
            for item in payload.get("headers", [])
        }

    def _extract_text(self, payload: dict) -> str:
        mime_type = payload.get("mimeType", "")
        body = payload.get("body", {})
        data = body.get("data")

        if mime_type == "text/plain" and data:
            return self._decode(data)

        plain_parts = []
        html_parts = []

        for part in payload.get("parts", []) or []:
            part_type = part.get("mimeType", "")

            if part_type.startswith("multipart/"):
                nested = self._extract_text(part)
                if nested:
                    plain_parts.append(nested)
                continue

            part_data = part.get("body", {}).get("data")
            if not part_data:
                continue

            decoded = self._decode(part_data)

            if part_type == "text/plain":
                plain_parts.append(decoded)
            elif part_type == "text/html":
                html_parts.append(decoded)

        if plain_parts:
            return "\n".join(plain_parts)

        if html_parts:
            return self._html_to_text(
                "\n".join(html_parts)
            )

        if data:
            decoded = self._decode(data)
            if mime_type == "text/html":
                return self._html_to_text(decoded)
            return decoded

        return ""

    @staticmethod
    def _decode(data: str) -> str:
        padding = "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode(
            data + padding
        ).decode("utf-8", errors="replace")

    @staticmethod
    def _html_to_text(value: str) -> str:
        value = re.sub(
            r"(?is)<(script|style).*?>.*?</\1>",
            " ",
            value,
        )
        value = re.sub(r"(?i)<br\s*/?>", "\n", value)
        value = re.sub(r"(?i)</p>", "\n", value)
        value = re.sub(r"<[^>]+>", " ", value)
        value = html.unescape(value)
        value = re.sub(r"[ \t]+", " ", value)
        value = re.sub(r"\n\s*\n+", "\n\n", value)
        return value.strip()
