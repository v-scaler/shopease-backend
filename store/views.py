import razorpay
from django.conf import settings
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets, permissions
from .models import Category, Product, CartItem, Order, OrderItem, Payment
from .serializers import CategorySerializer, ProductSerializer, CartItemSerializer, OrderSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def create_razorpay_order(self, request):
        user = request.user
        cart_items = CartItem.objects.filter(user=user)

        if not cart_items.exists():
            return Response({"error": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate total amount
        total_amount = sum(item.product.price * item.quantity for item in cart_items)

        # Create Order in DB with PENDING status
        order = Order.objects.create(user=user, total_amount=total_amount, status='PENDING')

        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price_at_purchase=cart_item.product.price
            )

        # Initialize Razorpay Client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Razorpay expects amount in paise (e.g., ₹100 = 10000 paise)
        razorpay_amount = int(total_amount * 100)
        
        razorpay_order = client.order.create({
            "amount": razorpay_amount,
            "currency": "INR",
            "payment_capture": "1"
        })

        # Save Payment record
        Payment.objects.create(
            order=order,
            razorpay_order_id=razorpay_order['id'],
            amount=total_amount,
            status='PENDING'
        )

        # Clear the user's cart after creating the order
        cart_items.delete()

        return Response({
            "order_id": order.id,
            "razorpay_order_id": razorpay_order['id'],
            "amount": total_amount,
            "currency": "INR",
            "key_id": settings.RAZORPAY_KEY_ID
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def verify_payment(self, request):
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response({"error": "Missing payment verification parameters."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
        except Payment.DoesNotExist:
            return Response({"error": "Payment record not found."}, status=status.HTTP_404_NOT_FOUND)

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            # Verify signature using Razorpay utility
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })

            # Update payment and order status upon successful verification
            payment.razorpay_payment_id = razorpay_payment_id
            payment.status = 'SUCCESS'
            payment.save()

            order = payment.order
            order.status = 'PAID'
            order.save()

            return Response({"message": "Payment verified successfully, order is now Paid."}, status=status.HTTP_200_OK)

        except razorpay.errors.SignatureVerificationError:
            payment.status = 'FAILED'
            payment.save()
            return Response({"error": "Invalid signature, payment verification failed."}, status=status.HTTP_400_BAD_REQUEST)
