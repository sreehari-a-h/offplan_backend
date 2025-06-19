from django.db import models

class City(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class District(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    city = models.ForeignKey(City, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class DeveloperCompany(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Property(models.Model):
    id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=255)
    cover = models.URLField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    address_text = models.CharField(max_length=255, blank=True, null=True)
    delivery_date = models.BigIntegerField(blank=True, null=True)
    min_area = models.IntegerField(blank=True, null=True)
    low_price = models.BigIntegerField(blank=True, null=True)

    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True)
    developer = models.ForeignKey(DeveloperCompany, on_delete=models.SET_NULL, null=True)

    property_type = models.CharField(max_length=100)
    property_status = models.CharField(max_length=100)
    sales_status = models.CharField(max_length=100)

    updated_at = models.DateTimeField()

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class AgentDetails(models.Model):
    id = models.BigAutoField(primary_key=True)
    username = models.TextField(unique=True)
    name = models.TextField()
    email = models.TextField(null=True, blank=True)
    whatsapp_number = models.TextField(null=True, blank=True)
    phone_number = models.TextField(null=True, blank=True)
    profile_image_url = models.TextField(null=True, blank=True)
    introduction_video_url = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    years_of_experience = models.TextField(null=True, blank=True)
    total_business_deals = models.TextField(null=True, blank=True)
    rank_top_performing = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    fa_name = models.TextField(null=True, blank=True)
    fa_description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'agent_details'
        unique_together = ('id', 'username')  # Matches composite PK in Supabase
        managed = False 

    def __str__(self):
        return self.username
