"""
Tests for investment APIs.
"""
from decimal import Decimal
from datetime import datetime
import tempfile
import os

from PIL import Image

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Investment, Tag, Activity

from investment.serializers import InvestmentSerializer, InvestmentDetailSerializer


INVESTMENTS_URL = reverse('investment:investment-list')


def detail_url(investment_id):
    """Create and return a investment detail URL."""
    return reverse('investment:investment-detail', args=[investment_id])


def image_upload_url(investment_id):
    """Create and return an image upload URL."""
    return reverse('investment:investment-upload-image', args=[investment_id])


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

    # add tags to investments tests
    def test_create_investment_with_new_tags(self):
        """Test creating a investment with new tags."""
        payload = {
            'ticker': 'IVV',
            'tags': [{'name': 'ETF'}, {'name': 'High Risk'}],
        }
        res = self.client.post(INVESTMENTS_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        investments = Investment.objects.filter(user=self.user)
        self.assertEqual(investments.count(), 1)
        investment = investments[0]
        self.assertEqual(investment.tags.count(), 2)
        for tag in payload['tags']:
            exists = investment.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_investment_with_existing_tags(self):
        """Test creating a investment with existing tag."""
        tag_crypto = Tag.objects.create(user=self.user, name='Crypto')
        payload = {
            'ticker': 'BTC',
            'tags': [{'name': 'Crypto'}, {'name': 'High Risk'}],
        }
        res = self.client.post(INVESTMENTS_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        investments = Investment.objects.filter(user=self.user)
        self.assertEqual(investments.count(), 1)
        investment = investments[0]
        self.assertEqual(investment.tags.count(), 2)
        self.assertIn(tag_crypto, investment.tags.all())
        for tag in payload['tags']:
            exists = investment.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    # updating tags on investments
    def test_create_tag_on_update(self):
        """Test create tag when updating a investment."""
        investment = create_investment(user=self.user)

        payload = {'tags': [{'name': 'Crypto'}]}
        url = detail_url(investment.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Crypto')
        self.assertIn(new_tag, investment.tags.all())

    def test_update_investment_assign_tag(self):
        """Test assigning an existing tag when updating a investment."""
        tag_crypto = Tag.objects.create(user=self.user, name='Crypto')
        investment = create_investment(user=self.user)
        investment.tags.add(tag_crypto)

        tag_etf = Tag.objects.create(user=self.user, name='ETF')
        payload = {'tags': [{'name': 'ETF'}]}
        url = detail_url(investment.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_etf, investment.tags.all())
        self.assertNotIn(tag_crypto, investment.tags.all())

    def test_clear_investment_tags(self):
        """Test clearing a investments tags."""
        tag = Tag.objects.create(user=self.user, name='Crypto')
        investment = create_investment(user=self.user)
        investment.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(investment.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(investment.tags.count(), 0)

    # add activities to investments tests
    def test_create_investment_with_new_activities(self):
        """Test creating an investment with new activities."""
        payload = {
            'ticker': 'TSLA2',
            'description': 'Sample description',
            'link': 'http://example.com/investment.pdf',
            'activities': [
                {
                    'trade_date': '2024-01-30T00:00:00Z',
                    'shares': 10,
                    'cost_per_share': 5,
                    'activity_type': 'BUY'
                },
                {
                    'trade_date': '2024-01-30T00:00:00Z',
                    'shares': 8,
                    'cost_per_share': 3,
                    'activity_type': 'BUY'
                }
            ],
        }
        res = self.client.post(INVESTMENTS_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        investments = Investment.objects.filter(user=self.user)
        self.assertEqual(investments.count(), 1)
        investment = investments[0]
        self.assertEqual(investment.activities.count(), 2)
        for activity in payload['activities']:
            exists = investment.activities.filter(
                investment=investment,
                user=self.user,
                trade_date=activity['trade_date'],
                shares=activity['shares'],
                cost_per_share=activity['cost_per_share'],
                activity_type=activity['activity_type'],
            ).exists()
            self.assertTrue(exists)

        payload2 = {
            'activities': [
                {
                    'trade_date': '2024-01-25T00:00:00Z',
                    'shares': 15,
                    'cost_per_share': 2,
                    'activity_type': 'BUY'
                }
            ],
        }
        url = detail_url(investment.id)
        res = self.client.patch(url, payload2, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_activity = Activity.objects.get(user=self.user, trade_date='2024-01-25T00:00:00Z', shares=15)
        self.assertIn(new_activity, investment.activities.all())

    def test_create_activity_on_investment_update(self):
        """Test creating an activity when updating an investment."""
        investment = create_investment(user=self.user)

        payload = {
            'activities': [
                {
                    'trade_date': '2024-01-25T00:00:00Z',
                    'shares': 15,
                    'cost_per_share': 2,
                    'activity_type': 'BUY'
                }
            ],
        }
        url = detail_url(investment.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_activity = Activity.objects.get(user=self.user, trade_date='2024-01-25T00:00:00Z', shares=15)
        self.assertIn(new_activity, investment.activities.all())

    def test_update_investment_with_new_activities(self):
        """Test creating an investment with new activities."""
        create_payload = {
            'ticker': 'TSLA2',
            'description': 'Sample description',
            'link': 'http://example.com/investment.pdf',
            'activities': [
                {
                    'trade_date': '2024-01-30T00:00:00Z',
                    'shares': 10,
                    'cost_per_share': 5,
                    'activity_type': 'BUY'
                },
                {
                    'trade_date': '2024-01-30T00:00:00Z',
                    'shares': 8,
                    'cost_per_share': 3,
                    'activity_type': 'BUY'
                }
            ],
        }
        res = self.client.post(INVESTMENTS_URL, create_payload, format='json')
        investments = Investment.objects.filter(user=self.user)
        investment = investments[0]

        update_payload = {
            'activities': [
                {
                    'trade_date': '2024-01-25T00:00:00Z',
                    'shares': 15,
                    'cost_per_share': 2,
                    'activity_type': 'BUY'
                }
            ],
        }
        url = detail_url(investment.id)
        res = self.client.patch(url, update_payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(investment.activities.all().count(), 3)


class ImageUploadTests(TestCase):
    """Tests for the image upload API."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user('user@example.com',  'password123')
        self.client.force_authenticate(self.user)
        self.investment = create_investment(user=self.user)

    def tearDown(self):
        self.investment.image.delete()

    def test_upload_image(self):
        """Test uploading an image to an investment."""
        url = image_upload_url(self.investment.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.investment.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.investment.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image."""
        url = image_upload_url(self.investment.id)
        payload = {'image': 'notanimage'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
