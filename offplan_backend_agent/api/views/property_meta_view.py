from django.shortcuts import render
from django.http import HttpResponse
from api.models import Property

def property_meta_view(request, username):
    property_id = request.GET.get("id")

    if not property_id:
        return HttpResponse("Property ID missing", status=400)

    try:
        property_obj = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        return HttpResponse("Property not found", status=404)

    return render(request, "property_meta.html", {
        "property": property_obj,
        "username": username,
    })

