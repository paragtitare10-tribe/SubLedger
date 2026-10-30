from rest_framework.routers import DefaultRouter

from .views import LedgerEntryViewSet

router = DefaultRouter()
router.register('', LedgerEntryViewSet, basename='ledger-entry')
urlpatterns = router.urls