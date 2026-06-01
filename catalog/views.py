from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema

from .serializers import (
    CategoryOutputSerializer,
    CategoryInputSerializer,
    SellerOutputSerializer,
    SellerInputSerializer,
    ProductOutputSerializer,
    ProductDetailOutputSerializer,
    ProductInputSerializer,
    ProductUpdateInputSerializer,
    VariantOutputSerializer,
    VariantInputSerializer,
    WarehouseOutputSerializer,
    WarehouseInputSerializer,
    InventoryOutputSerializer,
    InventoryInitializeInputSerializer,
    InventoryReconcileInputSerializer,
    InventoryReserveInputSerializer,
    ReservationOutputSerializer,
)
from .services import (
    create_category,
    create_seller,
    create_product,
    update_product,
    deactivate_product,
    create_variant,
    create_warehouse,
    initialise_inventory,
    reconcile_inventory,
    reserve_inventory,
    release_reservation,
    confirm_reservation,
)
from .selectors import (
    get_active_categories,
    get_category_by_slug,
    get_products,
    get_product_by_slug,
    get_products_by_seller,
    get_inventory_for_variant,
)
from .models import ProductVariant, InventoryReservation
from .exceptions import (
    CategoryNotFoundError,
    ProductNotFoundError,
    SellerAlreadyExistsError,
    DuplicateSkuError,
    DuplicateVariantError,
    InventoryNotFoundError,
    InsufficientStockError,
    InvalidInventoryOperationError,
    NegativeInventoryError,
)


# ── Category Views ────────────────────────────────────────────────────────────


class CategoryListCreateView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=CategoryOutputSerializer(many=True))
    def get(self, request):
        categories = get_active_categories()
        return Response(CategoryOutputSerializer(categories, many=True).data)

    @extend_schema(
        request=CategoryInputSerializer,
        responses=CategoryOutputSerializer
    )
    def post(self, request):
        serializer = CategoryInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            category = create_category(**serializer.validated_data)
        except CategoryNotFoundError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            CategoryOutputSerializer(category).data,
            status=status.HTTP_201_CREATED
        )


class CategoryDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=CategoryOutputSerializer)
    def get(self, request, slug):
        try:
            category = get_category_by_slug(slug=slug)
        except CategoryNotFoundError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(CategoryOutputSerializer(category).data)


# ── Seller Views ──────────────────────────────────────────────────────────────


class SellerCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=SellerInputSerializer,
        responses=SellerOutputSerializer
    )
    def post(self, request):
        serializer = SellerInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            seller = create_seller(
                user=request.user,
                **serializer.validated_data
            )
        except SellerAlreadyExistsError as e:
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(
            SellerOutputSerializer(seller).data,
            status=status.HTTP_201_CREATED
        )


# ── Product Views ─────────────────────────────────────────────────────────────


class ProductListCreateView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=ProductOutputSerializer(many=True))
    def get(self, request):
        products = get_products(
            category_slug=request.query_params.get('category'),
            brand=request.query_params.get('brand'),
            min_price=request.query_params.get('min_price'),
            max_price=request.query_params.get('max_price'),
            search=request.query_params.get('search'),
            ordering=request.query_params.get('ordering', '-created_at'),
            in_stock_only=request.query_params.get('in_stock', 'true').lower() == 'true',
        )
        return Response(ProductOutputSerializer(products, many=True).data)

    @extend_schema(
        request=ProductInputSerializer,
        responses=ProductDetailOutputSerializer
    )
    def post(self, request):
        serializer = ProductInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            seller = request.user.seller_profile
        except AttributeError:
            return Response(
                {'detail': 'You must create a seller profile first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            product = create_product(
                seller=seller,
                **serializer.validated_data
            )
        except CategoryNotFoundError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            ProductDetailOutputSerializer(product).data,
            status=status.HTTP_201_CREATED
        )


class ProductDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=ProductDetailOutputSerializer)
    def get(self, request, slug):
        try:
            product = get_product_by_slug(slug=slug)
        except ProductNotFoundError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductDetailOutputSerializer(product).data)

    @extend_schema(
        request=ProductUpdateInputSerializer,
        responses=ProductDetailOutputSerializer
    )
    def patch(self, request, slug):
        try:
            product = get_product_by_slug(slug=slug)
        except ProductNotFoundError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductUpdateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            product = update_product(
                product=product,
                **serializer.validated_data
            )
        except CategoryNotFoundError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductDetailOutputSerializer(product).data)


class ProductDeactivateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=None)
    def post(self, request, slug):
        try:
            product = get_product_by_slug(slug=slug)
        except ProductNotFoundError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)
        deactivate_product(product=product)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductVariantCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=VariantInputSerializer,
        responses=VariantOutputSerializer
    )
    def post(self, request, slug):
        try:
            product = get_product_by_slug(slug=slug)
        except ProductNotFoundError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)
        serializer = VariantInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            variant = create_variant(
                product=product,
                **serializer.validated_data
            )
        except DuplicateSkuError as e:
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)
        except DuplicateVariantError as e:
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(
            VariantOutputSerializer(variant).data,
            status=status.HTTP_201_CREATED
        )


class SellerProductsView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=ProductOutputSerializer(many=True))
    def get(self, request, seller_id):
        products = get_products_by_seller(seller_id=seller_id)
        return Response(ProductOutputSerializer(products, many=True).data)


# ── Warehouse Views ───────────────────────────────────────────────────────────


class WarehouseCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=WarehouseInputSerializer,
        responses=WarehouseOutputSerializer
    )
    def post(self, request):
        serializer = WarehouseInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        warehouse = create_warehouse(**serializer.validated_data)
        return Response(
            WarehouseOutputSerializer(warehouse).data,
            status=status.HTTP_201_CREATED
        )


# ── Inventory Views ───────────────────────────────────────────────────────────


class InventoryByVariantView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=InventoryOutputSerializer(many=True))
    def get(self, request, variant_id):
        try:
            variant = ProductVariant.objects.get(id=variant_id)
        except ProductVariant.DoesNotExist:
            return Response(
                {'detail': 'Variant not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        inventory = get_inventory_for_variant(variant=variant)
        return Response(InventoryOutputSerializer(inventory, many=True).data)


class InventoryInitializeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=InventoryInitializeInputSerializer,
        responses=InventoryOutputSerializer
    )
    def post(self, request):
        serializer = InventoryInitializeInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            variant = ProductVariant.objects.get(
                id=serializer.validated_data['variant_id']
            )
            from .models import Warehouse
            warehouse = Warehouse.objects.get(
                id=serializer.validated_data['warehouse_id']
            )
        except ProductVariant.DoesNotExist:
            return Response(
                {'detail': 'Variant not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Warehouse.DoesNotExist:
            return Response(
                {'detail': 'Warehouse not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            inventory = initialise_inventory(
                variant=variant,
                warehouse=warehouse,
                quantity=serializer.validated_data['quantity'],
            )
        except InvalidInventoryOperationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(
            InventoryOutputSerializer(inventory).data,
            status=status.HTTP_201_CREATED
        )


class InventoryReconcileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=InventoryReconcileInputSerializer,
        responses=InventoryOutputSerializer
    )
    def post(self, request):
        serializer = InventoryReconcileInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            variant = ProductVariant.objects.get(
                id=serializer.validated_data['variant_id']
            )
            from .models import Warehouse
            warehouse = Warehouse.objects.get(
                id=serializer.validated_data['warehouse_id']
            )
        except ProductVariant.DoesNotExist:
            return Response(
                {'detail': 'Variant not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Warehouse.DoesNotExist:
            return Response(
                {'detail': 'Warehouse not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            inventory = reconcile_inventory(
                variant=variant,
                warehouse=warehouse,
                quantity=serializer.validated_data['quantity'],
            )
        except InventoryNotFoundError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except InvalidInventoryOperationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(InventoryOutputSerializer(inventory).data)


class InventoryReserveView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=InventoryReserveInputSerializer,
        responses=ReservationOutputSerializer
    )
    def post(self, request):
        serializer = InventoryReserveInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            variant = ProductVariant.objects.get(
                id=serializer.validated_data['variant_id']
            )
            from .models import Warehouse
            warehouse = Warehouse.objects.get(
                id=serializer.validated_data['warehouse_id']
            )
        except ProductVariant.DoesNotExist:
            return Response(
                {'detail': 'Variant not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Warehouse.DoesNotExist:
            return Response(
                {'detail': 'Warehouse not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            reservation = reserve_inventory(
                variant=variant,
                warehouse=warehouse,
                quantity=serializer.validated_data['quantity'],
                idempotency_key=serializer.validated_data['idempotency_key'],
            )
        except InsufficientStockError as e:
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(
            ReservationOutputSerializer(reservation).data,
            status=status.HTTP_201_CREATED
        )


class ReservationReleaseView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=ReservationOutputSerializer)
    def post(self, request, reservation_id):
        try:
            reservation = InventoryReservation.objects.get(id=reservation_id)
        except InventoryReservation.DoesNotExist:
            return Response(
                {'detail': 'Reservation not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            release_reservation(reservation=reservation)
        except InvalidInventoryOperationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)
        reservation.refresh_from_db()
        return Response(ReservationOutputSerializer(reservation).data)


class ReservationConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=ReservationOutputSerializer)
    def post(self, request, reservation_id):
        try:
            reservation = InventoryReservation.objects.get(id=reservation_id)
        except InventoryReservation.DoesNotExist:
            return Response(
                {'detail': 'Reservation not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            confirm_reservation(reservation=reservation)
        except InvalidInventoryOperationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)
        except NegativeInventoryError as e:
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)
        reservation.refresh_from_db()
        return Response(ReservationOutputSerializer(reservation).data)
