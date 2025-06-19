from rest_framework.routers import DefaultRouter
from api.views.admin_agent_viewset import AdminAgentDetailViewSet

router = DefaultRouter()
router.register(r'admin/agents', AdminAgentDetailViewSet, basename='admin-agents')

urlpatterns = router.urls
