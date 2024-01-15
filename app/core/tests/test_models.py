"""
Tests for models.
"""
from decimal import Decimal
from datetime import datetime

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from core import models


def create_investment(user, **params):
    """Create and return a sample investment."""
    defaults = {
        'ticker': 'TSLA',
        'description': 'Sample description',
        'link': 'http://example.com/investment.pdf',
    }
    defaults.update(params)

    investment = models.Investment.objects.create(user=user, **defaults)
    return investment


def create_user(email='user@example.com', password='password123'):
    """Create a return a new user."""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test creating a user with an email is successful."""
        email = 'test123@example.com'
        password = 'password123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users."""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'password123')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test that creating a user without an email raises a ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'password123')

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = get_user_model().objects.create_superuser(
            'test123@example.com',
            'password123',
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    # investments
    def test_create_investment(self):
        """Test creating a investment is successful."""
        user = get_user_model().objects.create_user(
            'test@example.com',
            'password123',
        )
        investment = models.Investment.objects.create(
            user=user,
            ticker='Sample investment ticker',
            description='Sample investment description.',
        )

        self.assertEqual(str(investment), investment.ticker)

    # tags for investments
    def test_create_tag(self):
        """Test creating a tag is successful."""
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='Tag1')

        self.assertEqual(str(tag), tag.name)

    # activities for investments
    def test_create_activity(self):
        """Test creating an activity is successful."""
        user = create_user()
        investment = create_investment(user=user)

        naive_trade_datetime = datetime(2024, 1, 30)
        aware_datetime = timezone.make_aware(naive_trade_datetime, timezone=timezone.get_current_timezone())
        activity = models.Activity.objects.create(
            user=user,
            investment=investment,
            trade_date=aware_datetime,
            shares=10,
            cost_per_share=5,
            activity_type='BUY',
        )

        self.assertEqual(str(activity), 'BUY - TSLA')
