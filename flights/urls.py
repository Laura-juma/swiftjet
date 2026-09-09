from django.urls import path
from .views import home, BookFlight, BookingReview, search_flights, PaymentView, mpesa_callback

urlpatterns = [
    path("", home, name="home"),
    path("search/", search_flights, name="search_flights"),
    path("book-flight/<int:flight_id>/", BookFlight.as_view(), name="book"),
    path("booking-review/<int:booking_id>/", BookingReview.as_view(), name="booking_review"),
    path("payment/<int:booking_id>/", PaymentView, name="payment"),
    path("mpesa/callback/", mpesa_callback, name="mpesa_callback"),
]

