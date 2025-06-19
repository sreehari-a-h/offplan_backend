from rest_framework import serializers
from .models import AgentDetails

class AgentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentDetails
        fields = '__all__'
