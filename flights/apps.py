from django.apps import AppConfig

class FlightsConfig(AppConfig):
    name = "flights"

    def ready(self):
        from .signals import create_seats