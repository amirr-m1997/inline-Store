from django.urls import path

from .api import dashboard_summary

urlpatterns = [path("", dashboard_summary, name="dashboard-summary")]