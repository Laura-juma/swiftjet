from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import Flight, Seat

@receiver(post_save, sender=Flight)
def create_seats(sender, instance, created, **kwargs):

    if created:
        total_seats = instance.total_seats
        instance.available_seats = total_seats
        alphabet = ["A", "B", "C", "D", "E", "F"]
        generated_seats = []

        for index, i in enumerate(range(total_seats)):
            number = index + 1
            for letter in alphabet:
                seat_number = f"{number}{letter}"
                generated_seats.append(
                    Seat(
                        seat_number=seat_number,
                        flight=instance
                    )
                )
                if len(generated_seats) == total_seats:
                    break
            if len(generated_seats) == total_seats:
                break

        Seat.objects.bulk_create(generated_seats)

        Flight.objects.filter(pk=instance.pk).update(
            available_seats=total_seats
        )