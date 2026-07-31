from django import forms
from .models import Flight, Destination, Booking

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


SEAT_CHOICES = [
    ("1A", "1A"),
    ("1B", "1B"),
    ("1C", "1C"),
    ("1D", "1D"),
    ("2A", "2A"),
    ("2B", "2B"),
]



class BookFlightForm(forms.Form):
 

    seats = forms.IntegerField(min_value=1)
    seat_position = forms.ChoiceField(choices= SEAT_CHOICES)
