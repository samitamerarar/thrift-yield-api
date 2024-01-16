"""
Serializers for investment APIs
"""
from rest_framework import serializers

from core.models import Investment, Tag, Activity


class ActivitySerializer(serializers.ModelSerializer):
    """Serializer for activities."""

    class Meta:
        model = Activity
        fields = ['id', 'investment', 'trade_date', 'shares', 'cost_per_share', 'activity_type']
        read_only_fields = ['id']


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

    def _get_or_create_tags(self, tags, investment):
        """Handle getting or creating tags as needed."""
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(user=auth_user, **tag)
            investment.tags.add(tag_obj)

    def create(self, validated_data):
        """Create a investment."""
        tags = validated_data.pop('tags', [])
        investment = Investment.objects.create(**validated_data)
        self._get_or_create_tags(tags, investment)

        return investment

    def update(self, instance, validated_data):
        """Update investment."""
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class InvestmentDetailSerializer(InvestmentSerializer):
    """Serializer for investment detail view."""

    class Meta(InvestmentSerializer.Meta):
        fields = InvestmentSerializer.Meta.fields + ['description']
