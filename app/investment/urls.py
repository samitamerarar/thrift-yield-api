"""
URL mappings for the investment app.
"""
from django.urls import path, include

from rest_framework.routers import DefaultRouter

from investment import views


router = DefaultRouter()
router.register('investments', views.InvestmentViewSet)
router.register('tags', views.TagViewSet)

app_name = 'investment'

urlpatterns = [
    path('', include(router.urls)),
]
