from django.shortcuts import render, redirect
from django.views import View
from .models import Flight, Booking, Seat
from .forms import SearchFlightForm, BookFlightForm

def home(request):
  #because a form is a class like a model, you need to create an instance of it and then request.GET fills in that form with data
  form = SearchFlightForm(request.GET)
  flights = Flight.objects.none()

  if form.is_valid():
    arrival_destination = form.cleaned_data["arrival_destination"]
    departure_destination = form.cleaned_data["departure_destination"]
    departure_time = form.cleaned_data["departure_time"]

    flights = Flight.objects.filter(
            departure_destination=departure_destination,
            arrival_destination =arrival_destination,
            
        ) 

    if departure_time:
      flights = flights.filter(
        departure_time__date=departure_time)
   
  context = {
    "form" : form,
    "flights" : flights
  }


  return render(request, "flights/home.html", context)

class BookFlight(View):
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

        #creating the book object
        booking = Booking.objects.create(flight=flight)

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

  



      
        

