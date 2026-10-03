from rest_framework import serializers


class WarehouseQuerySerializer(serializers.Serializer):
    city = serializers.CharField(required=True)
    q = serializers.CharField(required=False, default="", allow_blank=True)
    type = serializers.ChoiceField(choices=["branch", "postomat"], default="branch")


class StreetQuerySerializer(serializers.Serializer):
    city = serializers.CharField(required=True)
    q = serializers.CharField(required=True, min_length=2)


class CityResultSerializer(serializers.Serializer):
    ref = serializers.CharField()
    name = serializers.CharField()
    area = serializers.CharField()
    label = serializers.CharField()  # type: ignore[assignment]


class WarehouseResultSerializer(serializers.Serializer):
    ref = serializers.CharField()
    city_ref = serializers.CharField()
    city_name = serializers.CharField()
    number = serializers.CharField()
    name = serializers.CharField()
    is_postomat = serializers.BooleanField()


class StreetResultSerializer(serializers.Serializer):
    ref = serializers.CharField()
    name = serializers.CharField()
    street_type = serializers.CharField()
    label = serializers.CharField()  # type: ignore[assignment]


class CitySearchResponseSerializer(serializers.Serializer):
    results = CityResultSerializer(many=True)


class WarehouseSearchResponseSerializer(serializers.Serializer):
    results = WarehouseResultSerializer(many=True)


class StreetSearchResponseSerializer(serializers.Serializer):
    results = StreetResultSerializer(many=True)


class DeliveryErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()
