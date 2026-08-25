from app.domain.enums import RecommendedAction


class ReplyGenerator:
    def generate(self, order, decision):
        name = order.customer.name.split()[0] if order else "there"
        number = order.order_number if order else "your order"
        action = decision.recommended_action

        if action == RecommendedAction.ORDER_STATUS_UPDATE:
            if order and order.fulfillment_status == "unfulfilled":
                return (
                    f"Hi {name}, I checked {number}. Your order has not shipped "
                    "yet, so tracking is not available at the moment. We can "
                    "share tracking once the order is fulfilled and carrier "
                    "information is added."
                )
            return (
                f"Hi {name}, I checked {number}. The current order status is "
                "available, but Shopify does not have tracking information for "
                "this order yet."
            )

        if action == RecommendedAction.SEND_TRACKING_UPDATE:
            tracking = (
                f" Tracking number: {order.tracking_number}."
                if order and order.tracking_number
                else ""
            )
            return (
                f"Hi {name}, I checked {number}. Here is the latest tracking "
                f"information currently available in the store.{tracking}"
            )

        if action == RecommendedAction.CARRIER_INVESTIGATION:
            return (
                f"Hi {name}, the tracking information for {number} has not "
                "moved for several days. Our team can review this for a carrier "
                "investigation and follow up with the next verified update."
            )

        if action == RecommendedAction.RETURN_REVIEW:
            return (
                f"Hi {name}, we found {number}. A team member will review the "
                "return request against the store policy before confirming any "
                "refund or next step."
            )

        if action == RecommendedAction.REPLACEMENT_REVIEW:
            return (
                f"Hi {name}, sorry about the issue with {number}. We will verify "
                "the order items and fulfillment details, then review the "
                "available replacement or refund options with you."
            )

        if action == RecommendedAction.CANCEL_REVIEW:
            return (
                f"Hi {name}, {number} has not started fulfillment. Your "
                "cancellation request is ready for a team member to review."
            )

        if action == RecommendedAction.MODIFY_REVIEW:
            return (
                f"Hi {name}, {number} has not started fulfillment. Your requested "
                "order change is ready for a team member to review."
            )

        if action == RecommendedAction.CANNOT_MODIFY:
            return (
                f"Hi {name}, fulfillment for {number} has already started, so we "
                "cannot guarantee the requested change. A team member can review "
                "the available options."
            )

        return (
            "Thanks for reaching out. A team member needs to review your request "
            "before we confirm the next step."
        )
