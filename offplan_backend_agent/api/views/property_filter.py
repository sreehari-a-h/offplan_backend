from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from api.models import Property
from api.serializers import PropertySerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .properties_list import CustomPagination

from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny

import calendar
from datetime import datetime
from django.db.models import Case, When, Value, IntegerField, Q, Sum, Prefetch, Count
import time
from django.db import connection, reset_queries

from django.db.models import Exists, OuterRef
from api.models import GroupedApartment


@method_decorator(csrf_exempt, name='dispatch')
@permission_classes([AllowAny])
class FilterPropertiesView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'city': openapi.Schema(type=openapi.TYPE_STRING),
                'district': openapi.Schema(type=openapi.TYPE_STRING),
                'property_type': openapi.Schema(type=openapi.TYPE_STRING),
                'unit_type': openapi.Schema(type=openapi.TYPE_STRING),
                'rooms': openapi.Schema(type=openapi.TYPE_STRING),
                'delivery_year': openapi.Schema(type=openapi.TYPE_INTEGER, description="Filter properties with delivery year >= this year"),
                'min_price': openapi.Schema(type=openapi.TYPE_INTEGER),
                'max_price': openapi.Schema(type=openapi.TYPE_INTEGER),
                'min_area': openapi.Schema(type=openapi.TYPE_INTEGER),
                'max_area': openapi.Schema(type=openapi.TYPE_INTEGER),
                'property_status': openapi.Schema(type=openapi.TYPE_STRING),
                'sales_status': openapi.Schema(type=openapi.TYPE_STRING),
                'title': openapi.Schema(type=openapi.TYPE_STRING, description="Filter by title"),
                'developer': openapi.Schema(type=openapi.TYPE_STRING, description="Filter by developer name"),
            },
        )
    )
    def post(self, request):
        reset_queries()
        start_time = time.time()
        
        data = request.data
        
        # Build queryset with all optimizations
        queryset = self._build_queryset(data)
        
        query_time = time.time() - start_time
        print(f"[FILTER] Query building time: {query_time:.2f}s, Queries: {len(connection.queries)}")
        
        # Paginate results with optimized pagination
        paginator = CustomPagination()
        paginator.request = request
        
        # Use only() to fetch only required fields for pagination
        paginated_qs = paginator.paginate_queryset(queryset, request)
        
        paginate_time = time.time() - start_time - query_time
        print(f"[FILTER] Pagination time: {paginate_time:.2f}s")
        
        serializer = PropertySerializer(paginated_qs, many=True)
        
        serialize_time = time.time() - start_time - query_time - paginate_time
        total_time = time.time() - start_time
        
        print(f"[FILTER] Serialization time: {serialize_time:.2f}s")
        print(f"[FILTER] Total time: {total_time:.2f}s, Total queries: {len(connection.queries)}")
        
        return paginator.get_paginated_response(serializer.data)

    def _build_queryset(self, data):
        """Build optimized queryset with all filters and annotations"""
        
        # Start with base queryset
        queryset = Property.objects.select_related(
            'city',
            'district',
            'developer',
            'property_type',
            'property_status',
            'sales_status'
        )
        
        # Apply filters
        queryset = self._apply_filters(queryset, data)
        
        # Apply ordering BEFORE annotation (important for performance)
        queryset = self._apply_ordering(queryset, data)
        
        # Add annotation last
        queryset = queryset.annotate(
            subunit_count=Sum('property_units__unit_count')
        )
        
        return queryset

    def _apply_filters(self, queryset, data):
        """Apply all filters to the queryset"""
        
        # Location filters
        if city := data.get("city"):
            queryset = queryset.filter(city__name__icontains=city)

        if district := data.get("district"):
            queryset = queryset.filter(district__name__icontains=district)

        # Property type filters
        if prop_type := data.get("property_type"):
            queryset = queryset.filter(property_type__name__icontains=prop_type)

        # Unit type filter - FIXED: Removed distinct(), use Exists properly
        if unit_type := data.get("unit_type"):
            subquery = GroupedApartment.objects.filter(
                property_id=OuterRef("pk"),
                unit_type__icontains=unit_type
            )
            queryset = queryset.filter(Exists(subquery))

        # Rooms filter - FIXED: Create proper subquery
        if rooms := data.get("rooms"):
            subquery = GroupedApartment.objects.filter(
                property_id=OuterRef("pk"),
                rooms=rooms
            )
            queryset = queryset.filter(Exists(subquery))

        # Delivery year filter
        if delivery_year := data.get("delivery_year"):
            queryset = self._filter_by_delivery_year(queryset, delivery_year)

        # Price filters
        if min_price := data.get("min_price"):
            queryset = queryset.filter(low_price__gte=min_price)
        if max_price := data.get("max_price"):
            queryset = queryset.filter(low_price__lte=max_price)

        # Area filters
        if min_area := data.get("min_area"):
            queryset = queryset.filter(min_area__gte=min_area)
        if max_area := data.get("max_area"):
            queryset = queryset.filter(min_area__lte=max_area)

        # Status filters
        if property_status := data.get("property_status"):
            queryset = queryset.filter(property_status__name__icontains=property_status)

        if sales_status := data.get("sales_status"):
            queryset = queryset.filter(sales_status__name__icontains=sales_status)

        # Developer filter
        if developer := data.get("developer"):
            queryset = queryset.filter(developer__name__icontains=developer)

        return queryset

    def _filter_by_delivery_year(self, queryset, delivery_year):
        """Filter properties by delivery year"""
        try:
            year = int(delivery_year)
            start_dt = datetime(year, 1, 1, 0, 0, 0)
            start_unix = calendar.timegm(start_dt.utctimetuple())

            if year < 2030:
                end_dt = datetime(year, 12, 31, 23, 59, 59)
                end_unix = calendar.timegm(end_dt.utctimetuple())
                return queryset.filter(
                    delivery_date__gte=start_unix,
                    delivery_date__lte=end_unix
                )
            else:
                return queryset.filter(delivery_date__gte=start_unix)

        except ValueError:
            return queryset

    def _apply_ordering(self, queryset, data):
        """Apply ordering to the queryset"""
        
        # Title filtering with prioritization
        if title := data.get("title"):
            queryset = queryset.annotate(
                title_priority=Case(
                    When(title__iexact=title, then=Value(0)),
                    When(title__icontains=title, then=Value(1)),
                    default=Value(2),
                    output_field=IntegerField(),
                )
            ).filter(
                Q(title__icontains=title)
            ).order_by('title_priority', '-updated_at')
        else:
            queryset = queryset.order_by("-updated_at")
            
        return queryset