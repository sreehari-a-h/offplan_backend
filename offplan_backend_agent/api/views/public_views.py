from rest_framework import viewsets
from api.models import AgentDetails
from api.serializers import AgentDetailSerializer

class PublicAgentDetailViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AgentDetail.objects.all()
    serializer_class = AgentDetailSerializer
