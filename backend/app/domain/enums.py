from enum import Enum


class Intent(str, Enum):
    WHERE_IS_MY_ORDER = "where_is_my_order"
    RETURN_REFUND = "return_refund"
    MISSING_WRONG_ITEM = "missing_wrong_item"
    CANCEL_MODIFY = "cancel_modify"
    UNKNOWN = "unknown"


class RecommendedAction(str, Enum):
    ORDER_STATUS_UPDATE = "order_status_update"
    SEND_TRACKING_UPDATE = "send_tracking_update"
    CARRIER_INVESTIGATION = "carrier_investigation"
    RETURN_REVIEW = "return_review"
    REPLACEMENT_REVIEW = "replacement_review"
    CANCEL_REVIEW = "cancel_review"
    MODIFY_REVIEW = "modify_review"
    CANNOT_MODIFY = "cannot_modify"
    MANUAL_REVIEW = "manual_review"


class CaseStatus(str, Enum):
    AWAITING_APPROVAL = "awaiting_approval"
    DECISION_READY = "decision_ready"
    APPROVED = "approved"
    REJECTED = "rejected"
    GMAIL_DRAFT_CREATED = "gmail_draft_created"
    GMAIL_SENT = "gmail_sent"
