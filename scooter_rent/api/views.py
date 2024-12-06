from django.conf import settings
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
import stripe
from .models import User, Location, Motorcycle, Rental, Payment, Review, Booking
from .serializers import UserSerializer, LocationSerializer, MotorcycleSerializer, RentalSerializer, PaymentSerializer, ReviewSerializer, BookingSerializer
from rest_framework.permissions import IsAuthenticated
from .serializers import UserRegistrationSerializer
from rest_framework.views import APIView
from rest_framework import status, permissions
from .serializers import MotorcycleRepairSerializer
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter



stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


@api_view(['POST'])
@authentication_classes([JWTAuthentication])  # Указываем использование JWT аутентификации
@permission_classes([IsAuthenticated])  # Требуем, чтобы пользователь был аутентифицирован
def create_payment_intent(request):
    try:
        rental_id = request.data.get('rental_id')

        if not rental_id:
            return JsonResponse({'error': 'Rental ID is required'}, status=400)

        # Получаем объект аренды
        rental = Rental.objects.get(id=rental_id)

        # Умножаем на 100, чтобы перевести сумму в центы
        amount = int(rental.total_price * 100)  # Преобразуем в целое число

        # Создание PaymentIntent с использованием Stripe API
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',  # Или используйте валюту аренды, если она у вас хранится
        )

        return JsonResponse({
            'client_secret': payment_intent.client_secret,
            'payment_intent': payment_intent.id
        })

    except Rental.DoesNotExist:
        return JsonResponse({'error': 'Rental not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def confirm_payment(request):
    payment_intent_id = request.POST.get('payment_intent_id')
    try:
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        # Проверяем статус платежа
        if payment_intent.status == 'succeeded':
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent.id)
            payment.payment_status = 'PAID'
            payment.save()

            return JsonResponse({'status': 'Payment successful'})
        else:
            return JsonResponse({'status': 'Payment failed'})
    except stripe.error.StripeError as e:
        return JsonResponse({'error': str(e)})

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer


class MotorcycleViewSet(viewsets.ModelViewSet):
    queryset = Motorcycle.objects.all()
    serializer_class = MotorcycleSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['serial_number']  # Фильтр по serial_number
    search_fields = ['serial_number']  # Поиск по serial_number

class RentalViewSet(viewsets.ModelViewSet):
    queryset = Rental.objects.all()
    serializer_class = RentalSerializer


from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils.timezone import now


@api_view(['POST'])
def process_mock_payment(request):
    rental_id = request.data.get('rental_id')
    card_number = request.data.get('card_number')
    expiry_date = request.data.get('expiry_date')
    cvv = request.data.get('cvv')

    # Простая проверка на наличие данных карты
    if not card_number or not expiry_date or not cvv:
        return Response({"error": "Card details are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        rental = Rental.objects.get(id=rental_id)

        # Проверяем, есть ли уже оплата
        if hasattr(rental, 'payment') and rental.payment.payment_status == 'PAID':
            return Response({"status": "Payment already completed."}, status=status.HTTP_400_BAD_REQUEST)

        # Mock-логика создания платежа
        payment = Payment.objects.create(
            rental=rental,
            amount=rental.total_price,
            payment_date=now(),
            payment_status='PAID',
            payment_method='MOCK',
        )

        return Response({
            "status": "Mock payment successful",
            "payment_id": payment.id,
            "card_last_4": card_number[-4:]  # Показываем только последние 4 цифры
        })
    except Rental.DoesNotExist:
        return Response({"error": "Rental not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class MotorcycleRepairViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]  # Только авторизованные пользователи (механики) могут обновлять информацию

    def partial_update(self, request, pk=None):
        try:
            motorcycle = Motorcycle.objects.get(pk=pk)
        except Motorcycle.DoesNotExist:
            return Response({'detail': 'Motorcycle not found'}, status=status.HTTP_404_NOT_FOUND)

        if not motorcycle.needs_repair:
            return Response({'detail': 'This motorcycle does not need repair'}, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, что пользователь является механиком
        if not request.user.is_staff:  # Если пользователь не механик, то выдаем ошибку
            return Response({'detail': 'You do not have permission to repair motorcycles'}, status=status.HTTP_403_FORBIDDEN)

        # Обновляем статус ремонта
        serializer = MotorcycleRepairSerializer(motorcycle, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Motorcycle repaired successfully'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



