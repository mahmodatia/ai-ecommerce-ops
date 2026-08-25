import json
from pathlib import Path
from app.domain.models import CustomerMessage

class MockGmail:
    def __init__(self, path: Path):
        self.path = path

    def list_messages(self):
        return [CustomerMessage.model_validate(x) for x in json.loads(self.path.read_text(encoding="utf-8"))]

    def get_message(self, message_id: str):
        return next((m for m in self.list_messages() if m.id == message_id), None)
