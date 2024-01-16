"""
Tests for the activities API.
"""
from datetime import datetime

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Activity, Investment

from investment.serializers import ActivitySerializer


ACTIVITIES_URL = reverse('investment:activity-list')


def detail_url(activity_id):
    """Create and return an activity detail URL."""
    return reverse('investment:activity-detail', args=[activity_id])


def create_activity(user, investment, **params):
    """Create and return a sample activity."""
    naive_trade_datetime = datetime(2024, 1, 30)
    aware_datetime = timezone.make_aware(naive_trade_datetime, timezone=timezone.get_current_timezone())
    defaults = {
        'trade_date': aware_datetime,
        'shares': 10,
        'cost_per_share': 5,
        'activity_type': 'BUY',
    }

    defaults.update(params)

    activity = Activity.objects.create(user=user, investment=investment, **defaults)
    return activity


def create_investment(user, **params):
    """Create and return a sample investment."""
    defaults = {
        'ticker': 'TSLA',
        'description': 'Sample description',
        'link': 'http://example.com/investment.pdf',
    }
    defaults.update(params)

    investment = Investment.objects.create(user=user, **defaults)
    return investment


def create_user(email='user@example.com', password='password123'):
    """Create and return user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicActivitiesApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving activities."""
        res = self.client.get(ACTIVITIES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateActivitiesApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.investment = create_investment(self.user)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_activities(self):
        """Test retrieving a list of activities."""
        create_activity(user=self.user, investment=self.investment, shares=6)
        create_activity(user=self.user, investment=self.investment, shares=18)

        res = self.client.get(ACTIVITIES_URL)

        activities = Activity.objects.all().order_by('-trade_date')
        serializer = ActivitySerializer(activities, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_activities_limited_to_user(self):
        """Test list of activities is limited to authenticated user."""
        user2 = create_user(email='user2@example.com')
        investment2 = create_investment(user2)
        create_activity(user=user2, investment=investment2, shares=10)
        activity = create_activity(user=self.user, investment=self.investment, shares=5)

        res = self.client.get(ACTIVITIES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['shares'], activity.shares)
        self.assertEqual(res.data[0]['id'], activity.id)

    def test_update_activity(self):
        """Test updating an activity."""
        activity = create_activity(user=self.user, investment=self.investment)

        payload = {'shares': 9}
        url = detail_url(activity.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        activity.refresh_from_db()
        self.assertEqual(activity.shares, payload['shares'])
