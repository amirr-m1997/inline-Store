from django.urls import path

from .api import advantage_list, hero_detail

urlpatterns = [path("hero/", hero_detail, name="site-hero"), path("advantages/", advantage_list, name="site-advantages")]
