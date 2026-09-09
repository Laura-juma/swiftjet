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

    return render(
        request,
        "flights/book.html",
        {
            "form": form,
            "flight": flight
        }
    )
    
  def post(self, request, flight_id):
    flight = Flight.objects.get(id=flight_id)
    form = BookFlightForm(request.POST)

    if form.is_valid():
        seats = form.cleaned_data["seats"]

        if seats > flight.available_seats:
            form.add_error("seats", "Not enough available seats.")
            return render(request, "flights/book.html", {
                "form": form,
                "flight": flight,
            })

        total_prices = flight.base_price * seats

        booking = Booking.objects.create(
            flight=flight,
            total_seat_prices=total_prices
        )

        self.update_remaining_seats(flight, seats)

        return redirect("booking_review", booking_id=booking.id)

    return render(request, "flights/book.html", {
        "form": form,
        "flight": flight,
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

            return HttpResponse(
                "STK Push sent successfully. Please complete the payment on your phone."
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

    # For now, we are not processing that data yet.
    # We first want to confirm that Safaricom can successfully
    # reach this endpoint.

    # Every HTTP request expects an HTTP response.
    # We return this JSON to acknowledge that we received
    # Safaricom's callback.
   data = json.loads(request.body)

   callback = data["Body"]["stkCallback"]

   process_callback(callback)

   print(data)

   return JsonResponse({
      "ResultCode" : 0,
      "ResultDesc" : "Accepted"
   })
