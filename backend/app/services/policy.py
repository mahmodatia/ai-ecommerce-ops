from __future__ import annotations

from app.domain.enums import Intent


POLICY_DEFINITIONS = {
    Intent.WHERE_IS_MY_ORDER: {
        "id": "shipping_wismo",
        "name": "Shipping / WISMO",
        "name_ar": "الشحن / أين طلبي؟",
        "version": "1.0",
        "status": "active",
        "summary": "Rules for order-status and tracking inquiries.",
        "summary_ar": "قواعد الاستفسار عن حالة الطلب والتتبع.",
        "content": (
            "Before fulfillment, tell the customer the order has not shipped "
            "and tracking may not exist yet. After fulfillment, standard "
            "delivery target is 3–5 business days. If tracking has no movement "
            "for 5 calendar days, recommend a carrier investigation review."
        ),
        "content_ar": (
            "قبل تنفيذ الطلب، أخبر العميل أن الطلب لم يتم شحنه بعد وقد لا تتوفر "
            "بيانات التتبع. بعد التنفيذ، يكون هدف التسليم المعتاد من 3 إلى 5 أيام "
            "عمل. إذا لم يتحرك التتبع لمدة 5 أيام تقويمية، أوصِ بمراجعة تحقيق مع شركة الشحن."
        ),
    },
    Intent.RETURN_REFUND: {
        "id": "returns_refunds",
        "name": "Returns / Refunds",
        "name_ar": "الإرجاع / الاسترداد",
        "version": "1.0",
        "status": "active",
        "summary": "Return-window and refund review constraints.",
        "summary_ar": "قيود فترة الإرجاع ومراجعة الاسترداد.",
        "content": (
            "Unused items may be returned within 30 calendar days of delivery. "
            "Refund decisions require human approval in this release."
        ),
        "content_ar": (
            "يمكن إرجاع العناصر غير المستخدمة خلال 30 يوماً تقويمياً من تاريخ التسليم. "
            "قرارات الاسترداد تتطلب موافقة بشرية في هذا الإصدار."
        ),
    },
    Intent.MISSING_WRONG_ITEM: {
        "id": "missing_wrong_item",
        "name": "Missing / Wrong Item",
        "name_ar": "عنصر ناقص / خاطئ",
        "version": "1.0",
        "status": "active",
        "summary": "Verification rules for missing or incorrect items.",
        "summary_ar": "قواعد التحقق من العناصر الناقصة أو الخاطئة.",
        "content": (
            "Verify order line items and fulfillment records. Replacement or "
            "refund recommendations require human approval and must not be "
            "executed automatically."
        ),
        "content_ar": (
            "تحقق من عناصر الطلب وسجلات التنفيذ. توصيات الاستبدال أو الاسترداد "
            "تتطلب موافقة بشرية ولا يجوز تنفيذها تلقائياً."
        ),
    },
    Intent.CANCEL_MODIFY: {
        "id": "cancel_modify",
        "name": "Cancel / Modify",
        "name_ar": "إلغاء / تعديل",
        "version": "1.0",
        "status": "active",
        "summary": "Eligibility rules for pre-fulfillment changes.",
        "summary_ar": "قواعد أهلية الإلغاء أو التعديل قبل بدء التنفيذ.",
        "content": (
            "Cancellation is eligible for review only before fulfillment starts. "
            "Modifications are not guaranteed after fulfillment begins. This "
            "system recommends actions but does not mutate Shopify orders."
        ),
        "content_ar": (
            "يكون طلب الإلغاء مؤهلاً للمراجعة فقط قبل بدء تنفيذ الطلب. ولا يمكن ضمان "
            "التعديلات بعد بدء التنفيذ. هذا النظام يقدم توصيات ولا يعدّل طلبات Shopify."
        ),
    },
}


def get_policy(intent: Intent) -> str | None:
    policy = POLICY_DEFINITIONS.get(intent)
    return policy["content"] if policy else None


def get_policy_definition(intent: Intent) -> dict | None:
    policy = POLICY_DEFINITIONS.get(intent)
    if not policy:
        return None
    return {**policy, "intent": intent.value}


def list_policies() -> list[dict]:
    return [
        {**value, "intent": intent.value}
        for intent, value in POLICY_DEFINITIONS.items()
    ]
