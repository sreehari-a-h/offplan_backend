from rest_framework import serializers
from .models import AgentDetails, Property
from api.models import Property, City, District, DeveloperCompany, Consultation, Subscription

class CitySerializerWithDistricts(serializers.ModelSerializer):
    districts = serializers.SerializerMethodField()
    class Meta:
        model = City
        fields = ["id", "name","districts"]
    def get_districts(self,obj):
        return [district.name for district in obj.districts.all()] 

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ["id", "name"]

class DistrictSerializer(serializers.ModelSerializer):
    city = CitySerializer()
    class Meta:
        model = District
        fields = ["id", "name", "city"]

class DeveloperCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeveloperCompany
        fields = ["id", "name"]

class PropertySerializer(serializers.ModelSerializer):
    city = CitySerializer()
    district = DistrictSerializer()
    developer = DeveloperCompanySerializer()

    class Meta:
        model = Property
        fields = [
            "id", "title", "cover", "address", "address_text",
            "delivery_date", "min_area", "low_price",
            "property_type", "property_status", "sales_status",
            "updated_at", "city", "district", "developer"
        ]


class AgentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentDetails
        fields = '__all__'

class ConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = '__all__'

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['email']