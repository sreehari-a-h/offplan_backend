from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models import AgentDetails
from api.serializers import AgentDetailSerializer

class AgentDetailByUsernameView(APIView):
    def get(self, request, username):
        try:
            agent = AgentDetails.objects.get(username=username)
            serializer = AgentDetailSerializer(agent)
            return Response(serializer.data)
        except AgentDetails.DoesNotExist:
            return Response({"detail": "Agent not found."}, status=status.HTTP_404_NOT_FOUND)
