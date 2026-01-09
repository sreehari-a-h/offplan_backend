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

import calendar
from datetime import datetime
from django.db.models import Case, When, Value, IntegerField, Q, Sum
import time
from django.db import connection, reset_queries

from rest_framework.pagination import PageNumberPagination
from collections import OrderedDict


class FastCountPagination(PageNumberPagination):
    """
    Optimized pagination that avoids slow COUNT(*) queries
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def paginate_queryset(self, queryset, request, view=None):
        self.count = None
        self.request = request
        
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        page_number = request.query_params.get(self.page_query_param, 1)
        try:
            page_number = int(page_number)
        except (TypeError, ValueError):
            page_number = 1

        if page_number < 1:
            page_number = 1

        offset = (page_number - 1) * page_size
        limit = page_size + 1

        results = list(queryset[offset:offset + limit])
        
        self.has_next = len(results) > page_size
        if self.has_next:
            results = results[:page_size]
        
        self.has_previous = page_number > 1
        self.page_number = page_number
        
        return results

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('page', self.page_number),
            ('page_size', self.get_page_size(self.request)),
            ('has_next', self.has_next),
            ('has_previous', self.has_previous),
            ('results', data)
        ]))

    def get_next_link(self):
        if not self.has_next:
            return None
        page_number = self.page_number + 1
        return self.request.build_absolute_uri(
            f'?{self.page_query_param}={page_number}'
        )

    def get_previous_link(self):
        if not self.has_previous:
            return None
        page_number = self.page_number - 1
        if page_number == 1:
            return self.request.build_absolute_uri('?')
        return self.request.build_absolute_uri(
            f'?{self.page_query_param}={page_number}'
        )


@method_decorator(csrf_exempt, name='dispatch')
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
        
        # Build queryset using the WORKING pattern from old version
        queryset = self._build_queryset(data)
        
        query_time = time.time() - start_time
        print(f"[FILTER] Query building time: {query_time:.2f}s, Queries: {len(connection.queries)}")
        
        # Use fast pagination
        paginator = FastCountPagination()
        paginator.request = request
        
        # Apply .distinct() like the old version to handle JOIN duplicates
        paginated_qs = paginator.paginate_queryset(queryset.distinct(), request)
        
        paginate_time = time.time() - start_time - query_time
        print(f"[FILTER] Pagination time: {paginate_time:.2f}s")
        
        # Serialize results
        serializer = PropertySerializer(paginated_qs, many=True)
        
        serialize_time = time.time() - start_time - query_time - paginate_time
        total_time = time.time() - start_time
        
        print(f"[FILTER] Serialization time: {serialize_time:.2f}s")
        print(f"[FILTER] Total time: {total_time:.2f}s, Total queries: {len(connection.queries)}")
        
        return paginator.get_paginated_response(serializer.data)

    def _build_queryset(self, data):
        """Build queryset using the WORKING pattern from old microservice"""
        
        # Start with annotation FIRST (like old version)
        queryset = Property.objects.annotate(
            subunit_count=Sum('property_units__unit_count')
        ).select_related(
            'city',
            'district',
            'developer',
            'property_type',
            'property_status',
            'sales_status'
        )
        
        # Apply filters
        queryset = self._apply_filters(queryset, data)
        
        # Apply ordering
        queryset = self._apply_ordering(queryset, data)
        
        return queryset

    def _apply_filters(self, queryset, data):
        """Apply all filters - using simple JOINs like old version, NOT Exists()"""
        
        # Location filters
        if city := data.get("city"):
            queryset = queryset.filter(city__name__icontains=city)

        if district := data.get("district"):
            queryset = queryset.filter(district__name__icontains=district)

        # Property type filters
        if prop_type := data.get("property_type"):
            queryset = queryset.filter(property_type__name__icontains=prop_type)

        # Unit type filter - USE SIMPLE JOIN like old version (NOT Exists)
        if unit_type := data.get("unit_type"):
            queryset = queryset.filter(grouped_apartments__unit_type__icontains=unit_type)

        # Rooms filter - USE SIMPLE JOIN like old version (NOT Exists)
        if rooms := data.get("rooms"):
            queryset = queryset.filter(grouped_apartments__rooms=rooms)

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
                    When(title__istartswith=title, then=Value(1)),
                    When(title__icontains=title, then=Value(2)),
                    default=Value(3),
                    output_field=IntegerField(),
                )
            ).filter(
                Q(title__icontains=title)
            ).order_by('title_priority', '-updated_at')
        else:
            queryset = queryset.order_by("-updated_at")
            
        return queryset