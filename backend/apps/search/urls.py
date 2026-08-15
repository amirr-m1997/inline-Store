from django.urls import path

from .api import unified_search

urlpatterns = [path("", unified_search, name="unified-search")]
