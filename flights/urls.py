from django.urls import path
from .views import home, BookFlight, BookingReview

urlpatterns = [
    path("", home, name="home"),
    path("book-flight/<int:flight_id>/", BookFlight.as_view(), name="book"),
    path("booking-review/<int:booking_id>/", BookingReview.as_view(), name="booking_review"),
]