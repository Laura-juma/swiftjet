from django.db import models

# Create your models here.
class Aircraft(models.Model):
  name = models.CharField(max_length = 100)
  model = models.CharField(max_length = 100)
  capacity = models.PositiveIntegerField()

  def __str__(self):
    return self.name

class Destination(models.Model):
  city = models.CharField(max_length = 100)
  country = models.CharField(max_length = 100)
  description = models.TextField()
  airport_code = models.CharField(max_length=5, unique=True)
  image = models.ImageField(upload_to="destinations/", blank=True, null=True)

  def __str__(self):
    return f"{self.city}, {self.country}"

class Flight(models.Model):
  flight_number = models.CharField(max_length = 100, unique=True)
  aircraft = models.ForeignKey(
    Aircraft,
    on_delete=models.CASCADE
  )

  departure_destination = models.ForeignKey(
    Destination,
     on_delete=models.CASCADE,
     related_name='departing_flights'
    )
  
  arrival_destination = models.ForeignKey(
    Destination,
    on_delete=models.CASCADE, 
    related_name='arriving_flights'
  )
  departure_time = models.DateTimeField()
  arrival_time = models.DateTimeField()
  base_price = models.DecimalField(max_digits=10, decimal_places=2)
  available_seats = models.PositiveIntegerField()

  STATUS_CHOICES = [
      ("On Time", "On Time"),
      ("Delayed", "Delayed"),
      ("Cancelled", "Cancelled"),
  ]

  status = models.CharField(
      max_length=20,
      choices = STATUS_CHOICES,
      default="On Time"
  )

  def __str__(self):
    return f"{self.flight_number} - {self.departure_destination} to {self.arrival_destination}"

class Booking(models.Model):

  flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name="bookings")
  total_seat_prices = models.DecimalField(max_digits=20, decimal_places = 2, default=0)

class Seat(models.Model):
  SEAT_CLASS_CHOICES =[
    ("Economy", "Economy"),
    ("Premium Economy", "Premium Economy"),
    ("Business", "Business"),
    ("First Class", "First Class"),

  ]

  seat_number = models.CharField(max_length = 5)
  flight = models.ForeignKey(
    Flight,
        on_delete=models.CASCADE,
        related_name="seats"
    )
  booking = models.ForeignKey(
        Booking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="seats"
    )

  seat_class=models.CharField(
    max_length = 20,
    choices = SEAT_CLASS_CHOICES,
    default = "Economy"
  )
  
  class Meta:
    unique_together = ("seat_number", "flight")

  def __str__(self):
    return f"Seat: {self.seat_number} on Flight: {self.flight.flight_number}"
