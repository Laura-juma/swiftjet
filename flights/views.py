from django.shortcuts import render
from .models import Flight
from .forms import SearchFlightForm

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
