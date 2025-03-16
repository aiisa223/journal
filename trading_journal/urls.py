from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'rules', views.TradeRuleViewSet, basename='traderule')
router.register(r'tags', views.TagViewSet, basename='tag')
router.register(r'trades', views.TradeViewSet, basename='trade')
router.register(r'journal', views.JournalEntryViewSet, basename='journal')
router.register(r'tag-categories', views.TagCategoryViewSet, basename='tagcategory')

urlpatterns = [
    path('', include(router.urls)),
] 