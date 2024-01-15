"""
Serializers for investment APIs
"""
from rest_framework import serializers

from core.models import Investment, Tag


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class InvestmentSerializer(serializers.ModelSerializer):
    """Serializer for investments."""
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Investment
        fields = ['id', 'ticker', 'link', 'tags']
        read_only_fields = ['id']

    def create(self, validated_data):
        """Create a investment."""
        tags = validated_data.pop('tags', [])
        investment = Investment.objects.create(**validated_data)
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            investment.tags.add(tag_obj)

        return investment


class InvestmentDetailSerializer(InvestmentSerializer):
    """Serializer for investment detail view."""

    class Meta(InvestmentSerializer.Meta):
        fields = InvestmentSerializer.Meta.fields + ['description']
