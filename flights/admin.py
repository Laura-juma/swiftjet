from django.contrib import admin
from flights.models import Aircraft, Destination, Flight, Booking

# Register your models here.
admin.site.register(Aircraft)
admin.site.register(Destination)
admin.site.register(Flight)
admin.site.register(Booking)
