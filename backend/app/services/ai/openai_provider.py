import re
from app.domain.models import CustomerMessage, EmailUnderstanding
from app.services.ai.prompts import SYSTEM_PROMPT

ORDER_RE = re.compile(r"#\d{4,}")

class OpenAIEngine:
    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        timeout: float = 20.0,
        retries: int = 3,
    ):
        from openai import OpenAI
        self.client = OpenAI(
            api_key=api_key,
            timeout=timeout,
            max_retries=max(0, retries),
        )
        self.model = model

    def analyze(self, message: CustomerMessage) -> EmailUnderstanding:
        response = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Sender: {message.sender_email}\nSubject: {message.subject}\n\n{message.body}"},
            ],
            text_format=EmailUnderstanding,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise RuntimeError("Model did not return parsed structured output.")

        # Ingestion metadata and deterministic order extraction are authoritative.
        parsed.customer_email = message.sender_email
        match = ORDER_RE.search(f"{message.subject}\n{message.body}")
        parsed.order_number = match.group(0) if match else None
        return parsed
