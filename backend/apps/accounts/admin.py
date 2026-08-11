from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomerAddress, User
@admin.register(User)
class StoreUserAdmin(UserAdmin):
    list_display = ("email", "phone", "first_name", "last_name", "is_active", "is_staff", "date_joined")
    list_filter = ("is_active", "is_staff", "groups")
    search_fields = ("username", "email", "phone", "first_name", "last_name")
    fieldsets = UserAdmin.fieldsets + (("اطلاعات مشتری", {"fields": ("phone", "landline", "customer_type", "company_name", "job_title", "national_id", "economic_code", "province", "city", "postal_code", "address")}),)

@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "province", "city", "is_default"); list_filter = ("is_default", "province"); search_fields = ("user__email", "user__phone", "recipient_name", "address")
