"""
Serializers for investment APIs
"""
from rest_framework import serializers

from core.models import Investment, Tag, Activity


class ActivitySerializer(serializers.ModelSerializer):
    """Serializer for activities."""

    class Meta:
        model = Activity
        fields = ['id', 'trade_date', 'shares', 'cost_per_share', 'activity_type']
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
    activities = ActivitySerializer(many=True, required=False)

    class Meta:
        model = Investment
        fields = ['id', 'ticker', 'link', 'tags', 'activities']
        read_only_fields = ['id']

    def _get_or_create_tags(self, tags_data, investment):
        """Handle getting or creating tags as needed."""
        auth_user = self.context['request'].user
        for tag_data in tags_data:
            tag_obj, created = Tag.objects.get_or_create(user=auth_user, **tag_data)
            investment.tags.add(tag_obj)

    def _create_activities(self, activities_data, investment):
        """Handle getting or creating tags as needed."""
        auth_user = self.context['request'].user
        for activity_data in activities_data:
            Activity.objects.create(user=auth_user, investment=investment, **activity_data)

    def create(self, validated_data):
        """Create an investment with tags and activities."""
        tags_data = validated_data.pop('tags', [])
        activities_data = validated_data.pop('activities', [])

        investment = Investment.objects.create(**validated_data)

        self._get_or_create_tags(tags_data, investment)
        self._create_activities(activities_data, investment)

        return investment

    def update(self, instance, validated_data):
        """Update investment."""
        tags_data = validated_data.pop('tags', None)
        activities_data = validated_data.pop('activities', None)

        if tags_data is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags_data, instance)

        if activities_data is not None:
            self._create_activities(activities_data, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class InvestmentDetailSerializer(InvestmentSerializer):
    """Serializer for investment detail view."""

    class Meta(InvestmentSerializer.Meta):
        fields = InvestmentSerializer.Meta.fields + ['description', 'image']


class InvestmentImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to investments."""

    class Meta:
        model = Investment
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': 'True'}}
