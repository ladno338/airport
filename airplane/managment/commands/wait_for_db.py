from django.utils import timezone
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from rest_framework.test import APIClient

from airport.models import Crew, Flight, Order, Ticket
from airport.serializers import FlightListSerializer, FlightDetailSerializer
from airport.tests.test_airplane_api import sample_airplane
from airport.tests.test_route_api import sample_route


FLIGHT_URL = reverse("airport:flight-list")


def remove_tickets_available(data):
    for instance in data:
        instance.pop("tickets_available")


def sample_crew(**params):
    defaults = {
        "first_name": "first",
        "last_name": "last",
    }
    defaults.update(params)
    return Crew.objects.create(**defaults)


def sample_flight(**params):
    defaults = {
        "route": sample_route(),
        "airplane": sample_airplane(),
        "departure_time": timezone.now(),
        "arrival_time": timezone.now() + timedelta(hours=5),
    }
    defaults.update(params)
    flight = Flight.objects.create(**defaults)
    crew = sample_crew()
    flight.crew.set([crew])
    return flight


def flight_detail_url(flight_id):
    return reverse("airport:flight-detail", args=[flight_id])


class UnauthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(FLIGHT_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_flights(self):
        sample_flight()
        sample_flight()

        flights = Flight.objects.order_by("id")
        serializer = FlightListSerializer(flights, many=True)

        response = self.client.get(FLIGHT_URL)
        remove_tickets_available(response.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_filter_flights_by_departure_time(self):
        flight_1 = sample_flight(departure_time="2023-12-12T08:00:00Z")
        flight_2 = sample_flight(departure_time="2023-12-13T08:00:00Z")

        response = self.client.get(FLIGHT_URL, {"departure_time": "2023-12-12"})

        remove_tickets_available(response.data)

        serializer_1 = FlightListSerializer(flight_1)
        serializer_2 = FlightListSerializer(flight_2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn(serializer_1.data, response.data)
        self.assertNotIn(serializer_2.data, response.data)

    def test_filter_flights_by_arrival_time(self):
        flight_1 = sample_flight(arrival_time="2023-12-12T08:00:00Z")
        flight_2 = sample_flight(arrival_time="2023-12-13T08:00:00Z")

        response = self.client.get(FLIGHT_URL, {"arrival_time": "2023-12-13"})

        remove_tickets_available(response.data)

        serializer_1 = FlightListSerializer(flight_1)
        serializer_2 = FlightListSerializer(flight_2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertNotIn(serializer_1.data, response.data)
        self.assertIn(serializer_2.data, response.data)

    def test_retrieve_flight_detail(self):
        flight = sample_flight()
        order = Order.objects.create(user=self.user)
        Ticket.objects.create(row=1, seat=1, flight=flight, order=order)
        Ticket.objects.create(row=2, seat=2, flight=flight, order=order)

        response = self.client.get(flight_detail_url(flight.id))

        serializer = FlightDetailSerializer(flight)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], flight.id)
        self.assertEqual(len(response.data["taken_places"]), 2)
        self.assertEqual(response.data, serializer.data)

    def test_create_flight_forbidden(self):
        payload = {
            "route": sample_route().id,
            "airplane": sample_airplane().id,
            "departure_time": timezone.now(),
            "arrival_time": timezone.now() + timedelta(hours=5),
        }
        response = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_flight_forbidden(self):
        payload = {
            "route": sample_route().id,
            "airplane": sample_airplane().id,
            "departure_time": timezone.now(),
            "arrival_time": timezone.now() + timedelta(hours=5),
        }

        flight = sample_flight()
        url = flight_detail_url(flight.id)

        response = self.client.put(url, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_flight_forbidden(self):
        flight = sample_flight()
        url = flight_detail_url(flight.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_flight(self):
        crew1 = sample_crew()
        crew2 = sample_crew()
        route1 = sample_route()
        airplane1 = sample_airplane()
        payload = {
            "crew": [crew1.id, crew2.id],
            "route": route1.id,
            "airplane": airplane1.id,
            "departure_time": timezone.now(),
            "arrival_time": timezone.now() + timedelta(hours=5),
        }

        response = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        flight = Flight.objects.get(id=response.data["id"])
        crews = flight.crew.all()

        route = flight.route
        del payload["route"]

        airplane = flight.airplane
        del payload["airplane"]

        self.assertEqual(crews.count(), 2)
        self.assertIn(crew1, crews)
        self.assertIn(crew2, crews)
        self.assertEqual(route1, route)
        self.assertEqual(airplane1, airplane)
