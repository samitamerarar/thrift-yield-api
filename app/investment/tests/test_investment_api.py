"""
Tests for investment APIs.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Investment

from investment.serializers import InvestmentSerializer, InvestmentDetailSerializer


INVESTMENTS_URL = reverse('investment:investment-list')


def detail_url(investment_id):
    """Create and return a investment detail URL."""
    return reverse('investment:investment-detail', args=[investment_id])


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


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicInvestmentAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(INVESTMENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateInvestmentApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='user@example.com',
            password='password123',
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_investments(self):
        """Test retrieving a list of investments."""
        create_investment(user=self.user)
        create_investment(user=self.user)

        res = self.client.get(INVESTMENTS_URL)

        investments = Investment.objects.all().order_by('-id')
        serializer = InvestmentSerializer(investments, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_investment_list_limited_to_user(self):
        """Test list of investments is limited to authenticated user."""
        other_user = create_user(
            email='other@example.com',
            password='password123',
        )
        create_investment(user=other_user)
        create_investment(user=self.user)

        res = self.client.get(INVESTMENTS_URL)

        investments = Investment.objects.filter(user=self.user)
        serializer = InvestmentSerializer(investments, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_investment_detail(self):
        """Test get investment detail."""
        investment = create_investment(user=self.user)

        url = detail_url(investment.id)
        res = self.client.get(url)

        serializer = InvestmentDetailSerializer(investment)
        self.assertEqual(res.data, serializer.data)

    def test_create_investment(self):
        """Test creating a investment."""
        payload = {
            'ticker': 'TSLA',
        }
        res = self.client.post(INVESTMENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        investment = Investment.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(investment, k), v)
        self.assertEqual(investment.user, self.user)

    def test_partial_update(self):
        """Test partial update of a investment."""
        original_link = 'https://example.com/investment.pdf'
        investment = create_investment(
            user=self.user,
            ticker='TSLA',
            link=original_link,
        )

        payload = {'ticker': 'AAPL'}
        url = detail_url(investment.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        investment.refresh_from_db()
        self.assertEqual(investment.ticker, payload['ticker'])
        self.assertEqual(investment.link, original_link)
        self.assertEqual(investment.user, self.user)

    def test_full_update(self):
        """Test full update of investment."""
        investment = create_investment(
            user=self.user,
            ticker='TSLA',
            link='https://example.com/investment.pdf',
            description='Sample investment description.',
        )

        payload = {
            'ticker': 'AAPL',
            'link': 'https://example.com/new-investment.pdf',
            'description': 'New investment description',
        }
        url = detail_url(investment.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        investment.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(investment, k), v)
        self.assertEqual(investment.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the investment user results in an error."""
        new_user = create_user(email='user2@example.com', password='password123')
        investment = create_investment(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(investment.id)
        self.client.patch(url, payload)

        investment.refresh_from_db()
        self.assertEqual(investment.user, self.user)

    def test_delete_investment(self):
        """Test deleting a investment successful."""
        investment = create_investment(user=self.user)

        url = detail_url(investment.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Investment.objects.filter(id=investment.id).exists())

    def test_investment_other_users_investment_error(self):
        """Test trying to delete another users investment gives error."""
        new_user = create_user(email='user2@example.com', password='password123')
        investment = create_investment(user=new_user)

        url = detail_url(investment.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Investment.objects.filter(id=investment.id).exists())