from django.urls import path
from .views import home, BookFlight

urlpatterns = [
    path("", home, name="home"),
    path("book-flight/<int:flight_id>/", BookFlight.as_view(), name="book")
]