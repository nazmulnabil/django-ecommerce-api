
from rest_framework import serializers
from .models import User, Address, Seller


# ── Output Serializers (read) ──────────────────────────

class AddressOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'label', 'street', 'city', 'country', 'postal_code', 'is_default']
        read_only_fields = fields


class SellerOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = ['id', 'store_name', 'is_verified', 'rating']
        read_only_fields = fields


class UserOutputSerializer(serializers.ModelSerializer):
    addresses = AddressOutputSerializer(many=True, read_only=True)
    seller_profile = SellerOutputSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'phone', 'profile_picture',
                  'addresses', 'seller_profile']
        read_only_fields = fields


# ── Input Serializers (write) ──────────────────────────

class UserRegistrationInputSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    phone = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_email(self, value):
        return value.lower().strip()


class UserProfileUpdateInputSerializer(serializers.Serializer):
    phone = serializers.CharField(required=False, allow_blank=True)
    username = serializers.CharField(max_length=150, required=False)


class AddressInputSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=50)
    street = serializers.CharField()
    city = serializers.CharField(max_length=100)
    country = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=20)
    is_default = serializers.BooleanField(default=False)


class SellerRegistrationInputSerializer(serializers.Serializer):
    store_name = serializers.CharField(max_length=255)


class LoginInputSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
class TokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()


class AuthResponseSerializer(serializers.Serializer):
    user = UserOutputSerializer()
    tokens = TokenSerializer()
    