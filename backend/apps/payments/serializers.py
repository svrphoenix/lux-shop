from rest_framework import serializers

from apps.payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "method",
            "status",
            "amount",
            "currency",
            "transaction_reference",
            "is_mock",
            "created_at",
        )
        read_only_fields = fields
