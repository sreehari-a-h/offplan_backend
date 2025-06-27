
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models import Property,PropertyStatus,SalesStatus
from api.serializers import PropertySerializer
from api.property_serializers import PropertyDetailSerializer  # Ensure this serializer is defined
from rest_framework.permissions import AllowAny
from django.db.models import Count
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

status_param = openapi.Parameter(
    'status',  # name of the query param
    openapi.IN_QUERY,  # it's a query param
    description="Filter by property status (e.g., Ready, Off Plan, Sold Out)",
    type=openapi.TYPE_STRING,
    required=True,
    enum=["Ready", "Off Plan", "Sold Out"],  # Optional enum
)
class PropertyByStatusView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(manual_parameters=[status_param])
    def get(self, request):
        status_name = request.query_params.get('status')
        if not status_name:
            return Response({
                "status": False,
                "message": "Missing 'status' query parameter",
                "data": [],
                "errors": None
            }, status=status.HTTP_200_OK)

        # Safely attempt to match either status
        property_status = PropertyStatus.objects.filter(name__iexact=status_name).first()
        sales_status = SalesStatus.objects.filter(name__iexact=status_name).first()

        if not property_status and not sales_status:
            return Response({
                "status": False,
                "message": f"No matching PropertyStatus or SalesStatus for '{status_name}'",
                "data": [],
                "errors": None
            }, status=status.HTTP_404_NOT_FOUND)

        # Filter properties based on which status matched
        if property_status:
            properties = Property.objects.filter(property_status=property_status)
        else:
            properties = Property.objects.filter(sales_status=sales_status)

        # Group by city
        city_data = (
            properties.values('city__id', 'city__name')
            .annotate(property_count=Count('id'))
            .order_by('city__name')
        )

        # Build response
        results = []
        for city in city_data:
            results.append({
                "city_id": city['city__id'],
                "city_name": city['city__name'],
                "property_count": city['property_count'],
                "filter_status": property_status.name if property_status else sales_status.name
            })

        return Response({
            "status": True,
            "message": f"Properties filtered by status '{status_name}'",
            "data": results,
            "errors": None
        },status=status.HTTP_200_OK)