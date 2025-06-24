import os
import django
import requests
import logging
from dateutil import parser as date_parser

# ✅ Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "backend.settings"))
django.setup()

# ✅ Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger()

# ✅ Import models
from api.models import Property, City, District, DeveloperCompany, PropertyType, PropertyStatus, SalesStatus

# ✅ Configuration
EXTERNAL_URL = "https://panel.estaty.app/api/v1/getProperties"
API_KEY = os.getenv("ESTATY_API_KEY")

if not API_KEY:
    raise RuntimeError("❌ Missing ESTATY_API_KEY environment variable.")

HEADERS = {
    "App-key": API_KEY,
    "Content-Type": "application/json",
}

# ✅ Helpers
def fetch_external_properties(page):
    url = EXTERNAL_URL if page == 1 else f"{EXTERNAL_URL}?page={page}"
    try:
        log.info(f"🌐 Fetching: {url}")
        response = requests.post(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        props = data.get("data") or []
        log.info(f"→ Got {len(props)} properties")
        return props
    except requests.RequestException as e:
        log.error(f"❌ Failed to fetch external properties (page {page}): {e}")
        return None

def is_different(internal, external):
    return (
        internal.title != external.get("title") or
        internal.description != external.get("description") or
        internal.cover != external.get("cover") or
        internal.address != external.get("address") or
        internal.delivery_date != external.get("delivery_date") or
        internal.completion_rate != external.get("completion_rate") or
        internal.residential_units != external.get("residential_units") or
        internal.commercial_units != external.get("commercial_units") or
        internal.payment_plan != external.get("payment_plan") or
        internal.post_delivery != external.get("post_delivery") or
        internal.payment_minimum_down_payment != external.get("payment_minimum_down_payment") or
        internal.guarantee_rental_guarantee != external.get("guarantee_rental_guarantee") or
        internal.guarantee_rental_guarantee_value != external.get("guarantee_rental_guarantee_value") or
        internal.downPayment != external.get("downPayment") or
        internal.low_price != external.get("low_price") or
        internal.min_area != external.get("min_area")
    )

def get_or_none(model, pk):
    try:
        return model.objects.get(pk=pk)
    except model.DoesNotExist:
        return None

def update_internal_property(internal, external):
    internal.title = external.get("title")
    internal.description = external.get("description")
    internal.cover = external.get("cover")
    internal.address = external.get("address")
    internal.delivery_date = external.get("delivery_date")
    internal.completion_rate = external.get("completion_rate")
    internal.residential_units = external.get("residential_units")
    internal.commercial_units = external.get("commercial_units")
    internal.payment_plan = external.get("payment_plan")
    internal.post_delivery = external.get("post_delivery")
    internal.payment_minimum_down_payment = external.get("payment_minimum_down_payment")
    internal.guarantee_rental_guarantee = external.get("guarantee_rental_guarantee")
    internal.guarantee_rental_guarantee_value = external.get("guarantee_rental_guarantee_value")
    internal.downPayment = external.get("downPayment")
    internal.low_price = external.get("low_price")
    internal.min_area = external.get("min_area")

    # Foreign keys
    internal.city = get_or_none(City, external.get("city"))
    internal.district = get_or_none(District, external.get("district"))
    internal.developer = get_or_none(DeveloperCompany, external.get("developer"))
    internal.property_type = get_or_none(PropertyType, external.get("property_type"))
    internal.property_status = get_or_none(PropertyStatus, external.get("property_status"))
    internal.sales_status = get_or_none(SalesStatus, external.get("sales_status"))

    # External updated_at
    updated_at_str = external.get("updated_at")
    if updated_at_str:
        internal.updated_at = date_parser.parse(updated_at_str)

    internal.save()

def main():
    page = 1
    updated_count = 0
    skipped_count = 0
    created_count = 0
    stop = False

    while not stop:
        props = fetch_external_properties(page)
        if props is None:
            log.warning("⚠️ Aborting due to fetch error.")
            break
        if not props:
            log.warning("⚠️ No more data.")
            break

        for ext in props:
            prop_id = ext.get("id")
            if not prop_id:
                continue

            try:
                internal = Property.objects.get(id=prop_id)
                external_updated = date_parser.parse(ext.get("updated_at"))

                if internal.updated_at == external_updated:
                    log.info(f"🛑 Match found on ID {prop_id}, stopping further sync.")
                    stop = True
                    break

                if is_different(internal, ext):
                    update_internal_property(internal, ext)
                    log.info(f"✅ Updated Property ID {prop_id}")
                    updated_count += 1
                else:
                    log.info(f"🔁 Skipped Property ID {prop_id} (no change)")
                    skipped_count += 1
            except Property.DoesNotExist:
                # Create new property
                log.info(f"➕ Creating new Property ID {prop_id}")
                new_property = Property(id=prop_id)
                update_internal_property(new_property, ext)
                created_count += 1

        page += 1

    log.info(f"\n✅ Sync Summary → Updated: {updated_count}, Created: {created_count}, Skipped: {skipped_count}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error(f"❌ Fatal error during sync: {e}")
