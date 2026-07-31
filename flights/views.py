from django.shortcuts import render, redirect
from django.views import View
from .models import Flight, Booking
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
    flight.available_seats =  flight.available_seats - seats
    flight.save()
  
  def get(self, request, flight_id):
    form = BookFlightForm()
    return render(request, 'flights/book.html', {'form': form})

  def post(self, request, flight_id):
    flight = Flight.objects.get(id=flight_id)
    form = BookFlightForm(request.POST)

    if form.is_valid():
        seats = form.cleaned_data["seats"]
        seat_position = form.cleaned_data["seat_position"]

        booking = Booking.objects.create(flight=flight, seats=seats, seat_position=seat_position)
        

        self.update_remaining_seats(flight, seats)

 
        return redirect("home")

   

  



      
        

