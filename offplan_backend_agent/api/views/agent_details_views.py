from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from api.models import AgentDetails
from api.serializers import AgentDetailSerializer
from api.permissions.is_admin_from_other_service import IsAdminFromOtherService

class AdminAgentDetailViewSet(viewsets.ModelViewSet):
    queryset = AgentDetail.objects.all()
    serializer_class = AgentDetailSerializer
    permission_classes = [IsAuthenticated, IsAdminFromOtherService]
