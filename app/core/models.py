"""
Database models.
"""
import uuid
import os

from django.conf import settings
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


def investment_image_file_path(instance, filename):
    """Generate file path for new investment image."""
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'

    return os.path.join('uploads', 'investment', filename)


class UserManager(BaseUserManager):
    """Manager for users."""

    def create_user(self, email, password=None, **extra_fields):
        """Create, save and return a new user."""
        if not email:
            raise ValueError('User must have an email address.')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Create and return a new superuser."""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system."""
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'


class Investment(models.Model):
    """Investment object."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    link = models.CharField(max_length=255, blank=True)
    tags = models.ManyToManyField('Tag')
    image = models.ImageField(null=True, upload_to=investment_image_file_path)

    def __str__(self):
        return self.ticker


class Tag(models.Model):
    """Tag for filtering investments."""
    name = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Activity(models.Model):
    """Trading activities for investments."""
    ACTIVITY_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, related_name='activities')
    trade_date = models.DateTimeField()
    shares = models.IntegerField()
    cost_per_share = models.DecimalField(max_digits=10, decimal_places=2)
    activity_type = models.CharField(max_length=4, choices=ACTIVITY_CHOICES)
    commission = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.activity_type} - {self.investment} - shares: {self.shares}"
