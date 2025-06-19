from rest_framework.views import APIView
from rest_framework.response import Response
from api.models import AgentDetails
from api.serializers import AgentDetailSerializer

class AgentListView(APIView):
    def get(self, request):
        agents = AgentDetails.objects.order_by('id')
        serializer = AgentDetailSerializer(agents, many=True)
        return Response(serializer.data)
