"""
Views for the investment APIs
"""
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Investment, Tag, Activity
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

        elif self.action == 'upload_image':
            return serializers.InvestmentImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new investment."""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to investment."""
        investment = self.get_object()
        serializer = self.get_serializer(investment, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BaseInvestmentAttrViewSet(
        mixins.DestroyModelMixin, mixins.UpdateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Base viewset for investment attributes."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


class TagViewSet(BaseInvestmentAttrViewSet):
    """Manage tags in the database."""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()

    def get_queryset(self):
        """Filter queryset to authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-name')


class ActivityViewSet(BaseInvestmentAttrViewSet):
    """Manage activities in the database."""
    serializer_class = serializers.ActivitySerializer
    queryset = Activity.objects.all()

    def get_queryset(self):
        """Retrieve activities for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-trade_date')
