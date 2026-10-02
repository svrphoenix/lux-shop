from apps.orders.models import Order
from apps.payments.models import (
    Payment,
    PaymentMethod,
    PaymentStatus,
)


def create_payment_for_order(order: Order, method: PaymentMethod) -> Payment:
    """Create a local payment record; card payments succeed only as a mock."""
    card_payment = method == PaymentMethod.CARD
    payment = Payment.objects.create(
        order=order,
        method=method,
        status=PaymentStatus.SUCCEEDED if card_payment else PaymentStatus.PENDING,
        amount=order.total_amount,
        transaction_reference=Payment.create_mock_reference() if card_payment else None,
        is_mock=card_payment,
    )

    if card_payment:
        order.status = Order.OrderStatus.PAID
        order.save(update_fields=["status", "updated_at"])

    return payment
