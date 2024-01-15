"""
Serializers for investment APIs
"""
from rest_framework import serializers

from core.models import Investment, Tag


class InvestmentSerializer(serializers.ModelSerializer):
    """Serializer for investments."""

    class Meta:
        model = Investment
        fields = ['id', 'ticker', 'link']
        read_only_fields = ['id']


class InvestmentDetailSerializer(InvestmentSerializer):
    """Serializer for investment detail view."""

    class Meta(InvestmentSerializer.Meta):
        fields = InvestmentSerializer.Meta.fields + ['description']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']
