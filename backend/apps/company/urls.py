from django.urls import path

from .api import company_detail

urlpatterns = [path("", company_detail, name="company-detail")]
