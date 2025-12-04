from django.shortcuts import render
from django.http import HttpResponse
from django.utils.html import strip_tags
from api.models import Property
import logging

logger = logging.getLogger(__name__)

def property_meta_view(request, username):
    """
    Renders Open Graph meta tags for property sharing on social media.
    Optimized for Facebook/WhatsApp crawlers with proper image handling.
    """
    property_id = request.GET.get("id")

    if not property_id:
        logger.error(f"Property ID missing for username: {username}")
        return HttpResponse("Property ID missing", status=400)

    try:
        property_obj = Property.objects.select_related(
            'city', 'district', 'developer', 'property_status'
        ).prefetch_related('property_images').get(id=property_id)
        
        logger.info(f"Property found: {property_obj.title} (ID: {property_id})")
        
    except Property.DoesNotExist:
        logger.error(f"Property not found: ID {property_id}")
        return HttpResponse("Property not found", status=404)

    # Get image URL with proper fallbacks
    image_url = None
    
    # Try property images first
    first_image = property_obj.property_images.first()
    if first_image and first_image.image:
        image_url = first_image.image
    
    # Fallback to cover image
    elif property_obj.cover:
        image_url = property_obj.cover
    
    # Ensure HTTPS and absolute URL
    if image_url:
        # If URL is relative, make it absolute
        if not image_url.startswith('http'):
            image_url = f"https://offplan.market{image_url}"
        # Ensure HTTPS
        elif image_url.startswith('http://'):
            image_url = image_url.replace('http://', 'https://')
    else:
        # Use a reliable static placeholder - REPLACE WITH YOUR ACTUAL STATIC IMAGE
        image_url = "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1200&h=630&fit=crop&q=80"
    
    logger.info(f"Using image URL: {image_url}")

    # Clean description (remove HTML tags)
    description = strip_tags(property_obj.description or "Luxury off-plan property in Dubai")[:160]

    # Build the frontend URL (ensure proper query parameter format)
    frontend_url = f"https://offplan.market/{username}/property-details/?id={property_obj.id}"

    # Format price
    formatted_price = f"AED {property_obj.low_price:,.0f}" if property_obj.low_price else "Contact for price"

    # Get property location safely
    city_name = property_obj.city.name if property_obj.city else "Dubai"
    district_name = property_obj.district.name if property_obj.district else ""

    context = {
        "property": property_obj,
        "username": username,
        "image_url": image_url,
        "description": description,
        "frontend_url": frontend_url,
        "formatted_price": formatted_price,
        "city_name": city_name,
        "district_name": district_name,
    }

    logger.info(f"Rendering property meta - Title: {property_obj.title}, Image: {image_url}")
    
    return render(request, "property_meta.html", context)