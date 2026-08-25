import re
from app.domain.enums import Intent
from app.domain.models import CustomerMessage, EmailUnderstanding

ORDER_RE = re.compile(r"#\d{4,}")

class RulesEngine:
    def analyze(self, message: CustomerMessage) -> EmailUnderstanding:
        text = f"{message.subject}\n{message.body}".lower()
        scores = {
            Intent.WHERE_IS_MY_ORDER: sum(p in text for p in ["where is", "tracking", "not arrived", "delayed", "delivery status"]),
            Intent.RETURN_REFUND: sum(p in text for p in ["return", "refund", "money back"]),
            Intent.MISSING_WRONG_ITEM: sum(p in text for p in ["missing", "wrong item", "wrong product", "wrong size", "only received"]),
            Intent.CANCEL_MODIFY: sum(p in text for p in ["cancel", "change address", "change size", "remove", "modify", "change my order"]),
        }
        intent = max(scores, key=scores.get)
        top = scores[intent]
        if top == 0:
            intent = Intent.UNKNOWN
            confidence = 0.35
        else:
            confidence = min(0.62 + 0.1 * top, 0.92)

        match = ORDER_RE.search(f"{message.subject}\n{message.body}")
        order_number = match.group(0) if match else None

        facts = []
        if order_number:
            facts.append(f"Customer referenced order {order_number}.")
        if intent == Intent.WHERE_IS_MY_ORDER:
            facts.append("Customer asks about delivery or tracking.")
        elif intent == Intent.RETURN_REFUND:
            facts.append("Customer requests a return or refund.")
        elif intent == Intent.MISSING_WRONG_ITEM:
            facts.append("Customer reports a missing or incorrect item.")
        elif intent == Intent.CANCEL_MODIFY:
            if "cancel" in text:
                facts.append("Customer requests cancellation.")
            else:
                facts.append("Customer requests an order modification.")

        return EmailUnderstanding(
            intent=intent,
            order_number=order_number,
            customer_email=message.sender_email,
            confidence=confidence,
            facts=facts,
            requires_policy_lookup=intent in {
                Intent.RETURN_REFUND,
                Intent.MISSING_WRONG_ITEM,
                Intent.CANCEL_MODIFY,
            },
        )
