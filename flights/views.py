from django.shortcuts import render, redirect
from django.views import View
from .models import Flight, Booking, Seat
from .forms import SearchFlightForm, BookFlightForm
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse,HttpResponse
import json
from .services.mpesa import process_callback, stk_push
from django.urls import reverse

def home(request):
    form = SearchFlightForm()
    return render(request, "flights/home.html", {"form": form})

def search_flights(request):
    form = SearchFlightForm(request.GET)
    flights = Flight.objects.none()

    if form.is_valid():
        arrival_destination = form.cleaned_data["arrival_destination"]
        departure_destination = form.cleaned_data["departure_destination"]
        departure_time = form.cleaned_data["departure_time"]

        flights = Flight.objects.filter(
            departure_destination=departure_destination,
            arrival_destination=arrival_destination,
        )

        if departure_time:
            flights = flights.filter(
                departure_time__date=departure_time
            )

    return render(request, "flights/search_results.html", {
        "form": form,
        "flights": flights,
    })

class BookFlight(View):
  
  def calculate_price(self, flight, seat_position):
     seat_prices=[]
     total_seats_price = Decimal("0.00")
     for seat in seat_position:      
        if seat.seat_class == "Premium Economy":
           seat_price = flight.base_price * Decimal("1.5")
        elif seat.seat_class == "Business":
           seat_price = flight.base_price * Decimal("1.8")
        elif seat.seat_class == "First Class":
            seat_price = flight.base_price * Decimal("2.5")
        else:
           seat_price = flight.base_price

        seat_prices.append({
           "seat" : seat,
           "price" : seat_price
        })
        
        total_seats_price = total_seats_price + seat_price
        
     
     return seat_prices, total_seats_price      
        
  def update_remaining_seats(self, flight, seats):
    flight.available_seats -= seats
    flight.save()
  
  def get(self, request, flight_id):
    flight = Flight.objects.get(id=flight_id)
    form = BookFlightForm()

    seats = flight.seats.all()

    for seat in seats:
     seat.row_number = int(seat.seat_number[:-1])

    return render(
        request,
        "flights/book.html",
        {
            "form": form,
            "flight": flight,
            "seats" : seats
        }
    )
    
def post(self, request, flight_id):
    flight = Flight.objects.get(id=flight_id)

    # Get selected seats from JavaScript
    selected_seats = json.loads(request.body)["seats"]

    if len(selected_seats) > flight.available_seats:
        return JsonResponse({
            "success": False,
            "message": "Not enough seats available."
        })

    # Check whether the selected seats are already booked
    for seat in selected_seats:
        specific_seat = Seat.objects.get(
            seat_number=seat,
            flight=flight
        )

        if specific_seat.booking:
            return JsonResponse({
                "success": False,
                "message": "Seat is already booked"
            })

    # All seats are available, so create ONE booking
    booking = Booking.objects.create(flight=flight)

    # Assign all selected seats to the booking
    for seat in selected_seats:
        specific_seat = Seat.objects.get(
            seat_number=seat,
            flight=flight
        )

        specific_seat.booking = booking
        specific_seat.save()

    # Calculate seat price
    base_price = flight.base_price
    total_prices = base_price * len(selected_seats)
    booking.total_seat_prices = total_prices
    booking.save()

    #updating available seats
    flight.available_seats -= len(selected_seats)
    flight.save()
    

    return JsonResponse({
        "success": True,
        "redirect_url": reverse(
            "booking_review",
            args=[booking.id]
        )
    })
  
class BookingReview(View): 
    def get(self, request, booking_id):

        booking = Booking.objects.get(id=booking_id)

        return render(
            request,
            "flights/booking_review.html",
            {
                "booking": booking
            }
        )

def PaymentView(request, booking_id):

    booking = Booking.objects.get(id=booking_id)

    if request.method == "GET":

        return render(
            request,
            "flights/payment.html",
            {
                "booking": booking
            }
        )

    elif request.method == "POST":

        phone_number = request.POST.get("phone_number")

        try:
            response = stk_push(
                phone_number=phone_number,
                amount=int(booking.total_seat_prices),
                account_reference=f"Booking-{booking.id}",
                transaction_desc="SwiftJet Flight Booking",
            )

            booking.checkout_request_id = response["CheckoutRequestID"]
            booking.merchant_request_id = response["MerchantRequestID"]
            booking.save()

            return render(request, "flights/payment.html", {
               "booking" : booking,
              
            }
                
            )

        except Exception as e:
           return HttpResponse(str(e), status=500)
           
@csrf_exempt
@require_POST
def mpesa_callback(request):
    # Safaricom initiates a NEW HTTP request to this view. It would have been a response but it cant because the other conversation ended (stk_push) so only way is by sending a request  to start a conversation to tell us how the payment went. remember the stk_push response only tells us that our request has been recieved nothing about the user's payment.
    # after it finishes processing the customer's payment.

    # The payment result (success, cancelled, timeout, etc.)
    # will be sent inside request.body as JSON.

    

    # Every HTTP request expects an HTTP response.
    # We return this JSON to acknowledge that we received
    # Safaricom's callback.
   print("🔥🔥🔥 MPESA CALLBACK RECEIVED 🔥🔥🔥")
   data = json.loads(request.body)

   callback = data["Body"]["stkCallback"]

   process_callback(callback)

   print(data)

   return JsonResponse({
      "ResultCode" : 0,
      "ResultDesc" : "Accepted"
   })

def payment_status(request, booking_id):
   booking = Booking.objects.get(id=booking_id)

   return JsonResponse({
      "status" : booking.payment_status
   })

#TESTING
def database_test(request):
    return JsonResponse({
        "flights": Flight.objects.count(),
    })

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from .models import Aircraft, Destination, Flight


@staff_member_required
def setup_production(request):

    if request.method != "POST":
        return JsonResponse({
            "error": "POST request required."
        }, status=405)

    # Aircraft
    falcon = Aircraft.objects.create(
        name="SwiftJet Falcon",
        model="Boeing 737-800",
        capacity=189
    )

    eagle = Aircraft.objects.create(
        name="SwiftJet Eagle",
        model="Boeing 787-8 Dreamliner",
        capacity=234
    )

    horizon = Aircraft.objects.create(
        name="SwiftJet Horizon",
        model="Embraer E190",
        capacity=96
    )

    # Destinations
    nairobi = Destination.objects.create(
        city="Nairobi",
        country="Kenya",
        description="Kenya's vibrant capital city.",
        airport_code="NBO"
    )

    mombasa = Destination.objects.create(
        city="Mombasa",
        country="Kenya",
        description="A beautiful coastal city known for its beaches and Swahili culture.",
        airport_code="MBA"
    )

    kisumu = Destination.objects.create(
        city="Kisumu",
        country="Kenya",
        description="A lakeside city on the shores of Lake Victoria.",
        airport_code="KIS"
    )

    eldoret = Destination.objects.create(
        city="Eldoret",
        country="Kenya",
        description="A city in Kenya's Rift Valley known as the City of Champions.",
        airport_code="EDL"
    )

    dubai = Destination.objects.create(
        city="Dubai",
        country="UAE",
        description="A major international destination known for its modern architecture and attractions.",
        airport_code="DXB"
    )

    london = Destination.objects.create(
        city="London",
        country="United Kingdom",
        description="A major international city and global travel destination.",
        airport_code="LHR"
    )

    # Flights
    flights = [
        {
            "flight_number": "SJ101",
            "aircraft": falcon,
            "departure_destination": nairobi,
            "arrival_destination": mombasa,
            "base_price": 6500,
        },
        {
            "flight_number": "SJ102",
            "aircraft": falcon,
            "departure_destination": mombasa,
            "arrival_destination": nairobi,
            "base_price": 6500,
        },
        {
            "flight_number": "SJ201",
            "aircraft": eagle,
            "departure_destination": nairobi,
            "arrival_destination": dubai,
            "base_price": 45000,
        },
        {
            "flight_number": "SJ301",
            "aircraft": eagle,
            "departure_destination": nairobi,
            "arrival_destination": london,
            "base_price": 82000,
        },
        {
            "flight_number": "SJ401",
            "aircraft": horizon,
            "departure_destination": nairobi,
            "arrival_destination": kisumu,
            "base_price": 5000,
        },
        {
            "flight_number": "SJ402",
            "aircraft": horizon,
            "departure_destination": nairobi,
            "arrival_destination": eldoret,
            "base_price": 4800,
        },
        {
            "flight_number": "SJ404",
            "aircraft": eagle,
            "departure_destination": nairobi,
            "arrival_destination": london,
            "base_price": 89000,
        },
    ]

    for flight_data in flights:
        Flight.objects.create(
            **flight_data,
            departure_time=timezone.now() + timedelta(days=7),
            arrival_time=timezone.now() + timedelta(days=7, hours=2),
            available_seats=flight_data["aircraft"].capacity,
            total_seats=flight_data["aircraft"].capacity,
            status="On Time"
        )

    return JsonResponse({
        "success": True,
        "message": "Production database populated successfully."
    })

from django.http import JsonResponse
from django.contrib.auth.models import User


import os


def create_production_superuser(request):
    if request.method != "POST":
        return JsonResponse({
            "error": "POST request required."
        }, status=405)

    secret = request.POST.get("secret")

    if secret != os.environ.get("PRODUCTION_SETUP_SECRET"):
        return JsonResponse({
            "error": "Invalid secret."
        }, status=403)

    username = os.environ.get("PRODUCTION_ADMIN_USERNAME")
    email = os.environ.get("PRODUCTION_ADMIN_EMAIL")
    password = os.environ.get("PRODUCTION_ADMIN_PASSWORD")

    if User.objects.filter(username=username).exists():
        return JsonResponse({
            "message": "Superuser already exists."
        })

    User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )

    return JsonResponse({
        "success": True,
        "message": "Production superuser created."
    })