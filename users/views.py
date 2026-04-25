# users/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema

from .serializers import (
    UserRegistrationInputSerializer,
    UserProfileUpdateInputSerializer,
    AddressInputSerializer,
    SellerRegistrationInputSerializer,
    LoginInputSerializer,
    UserOutputSerializer,
    AddressOutputSerializer,
    SellerOutputSerializer,
    AuthResponseSerializer,
)
from .services import (
    register_user,
    authenticate_user,
    update_user_profile,
    create_address,
    set_default_address,
    delete_address,
    register_seller,
)
from .selectors import get_addresses_for_user
from .exceptions import (
    EmailAlreadyExistsError,
    AddressNotFoundError,
    SellerAlreadyExistsError,
    InvalidCredentialsError,
)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=UserRegistrationInputSerializer, responses=AuthResponseSerializer)
    def post(self, request):
        serializer = UserRegistrationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = register_user(**serializer.validated_data)
        except EmailAlreadyExistsError as e:
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserOutputSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=LoginInputSerializer, responses=AuthResponseSerializer)
    def post(self, request):
        serializer = LoginInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = authenticate_user(**serializer.validated_data)
        except InvalidCredentialsError as e:
            return Response({'detail': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserOutputSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserOutputSerializer)
    def get(self, request):
        return Response(UserOutputSerializer(request.user).data)

    @extend_schema(request=UserProfileUpdateInputSerializer, responses=UserOutputSerializer)
    def patch(self, request):
        serializer = UserProfileUpdateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = update_user_profile(user=request.user, **serializer.validated_data)
        return Response(UserOutputSerializer(user).data)


class AddressListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=AddressOutputSerializer(many=True))
    def get(self, request):
        addresses = get_addresses_for_user(user=request.user)
        return Response(AddressOutputSerializer(addresses, many=True).data)

    @extend_schema(request=AddressInputSerializer, responses=AddressOutputSerializer)
    def post(self, request):
        serializer = AddressInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        address = create_address(user=request.user, **serializer.validated_data)
        return Response(AddressOutputSerializer(address).data, status=status.HTTP_201_CREATED)


class AddressDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=AddressInputSerializer, responses=AddressOutputSerializer)
    def patch(self, request, address_id):
        try:
            address = set_default_address(user=request.user, address_id=address_id)
        except AddressNotFoundError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(AddressOutputSerializer(address).data)

    @extend_schema(responses=None)
    def delete(self, request, address_id):
        try:
            delete_address(user=request.user, address_id=address_id)
        except AddressNotFoundError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SellerRegisterView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=SellerRegistrationInputSerializer, responses=SellerOutputSerializer)
    def post(self, request):
        serializer = SellerRegistrationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            seller = register_seller(user=request.user, **serializer.validated_data)
        except SellerAlreadyExistsError as e:
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)

        return Response(SellerOutputSerializer(seller).data, status=status.HTTP_201_CREATED)