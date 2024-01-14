"""
Views for the investment APIs
"""
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Investment
from investment import serializers


class InvestmentViewSet(viewsets.ModelViewSet):
    """View for manage investment APIs."""
    serializer_class = serializers.InvestmentDetailSerializer
    queryset = Investment.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Retrieve investments for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return serializers.InvestmentSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new investment."""
        serializer.save(user=self.request.user)
