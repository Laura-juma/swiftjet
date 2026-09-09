from django import forms
from .models import Flight, Destination, Booking, Seat

class SearchFlightForm(forms.Form):

    departure_destination = forms.ModelChoiceField(
        queryset=Destination.objects.all(),
        widget=forms.Select(attrs={
            "class": "form-select"
        }),
        empty_label ="From",
        required=True
    )
    
    arrival_destination = forms.ModelChoiceField(
        queryset=Destination.objects.all(),
        widget=forms.Select(attrs={
            "class": "form-select"
        }),
        empty_label="To",
        required=True
    )

    departure_time = forms.DateField(
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date"
        }),
        required=False
    )

class BookFlightForm(forms.Form):
    seats = forms.IntegerField(
        min_value=1,
        label="Number of Seats")
    
#   seat_position = forms.ModelMultipleChoiceField(
#       queryset = Seat.objects.none(),
#       widget = forms.CheckboxSelectMultiple,
#       label = "Seat Positions"
#   )


