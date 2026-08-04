from django.shortcuts import render, redirect
from django.views import View
from .models import Flight, Booking, Seat
from .forms import SearchFlightForm, BookFlightForm
from decimal import Decimal


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
        elif seat.seat_class == "First class":
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
    form.fields["seat_position"].queryset = Seat.objects.filter(
      flight = flight,
      booking__isnull = True
    )
    return render(request, 'flights/book.html', {'form': form,
                                                 "flight": flight})

  def post(self, request, flight_id):
    flight = Flight.objects.get(id=flight_id)
    form = BookFlightForm(request.POST)
    form.fields["seat_position"].queryset = Seat.objects.filter(
          flight = flight,
          booking__isnull = True
        )

    if form.is_valid():
        seats = form.cleaned_data["seats"]
        seat_position = form.cleaned_data["seat_position"]

        #Check if number of seats required is greater than available seats. If greater, show error message and render the form again

        if seats > flight.available_seats:
            form.add_error("seats", "Not enough available seats.")
            return render(request, "flights/book.html", {
              "form": form,
              "flight": flight,
          })

        #Check if number of seats selected is equal to the seat_positions selected, if not, show error message and render the form again

        if seat_position.count() != seats:
          form.add_error("seat_position", "Please select the correct number of seats")

          return render(request, "flights/book.html", {
              "form": form,
              "flight": flight,
          })

        #calculating each seat price
        seat_prices, total_prices =self.calculate_price(flight, seat_position)

        #creating the book object
        booking = Booking.objects.create(flight=flight, total_seat_prices = total_prices)

        #updating the seat objects to include the specific booking object
        for seat in seat_position :
          seat.booking = booking
          seat.save()
        
        

        self.update_remaining_seats(flight, seats)

 
        return redirect("booking_review",
                        booking_id = booking.id)

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





      
        

