from django.urls import path

from .api import contact_message_create, footer_detail, navigation_list

urlpatterns = [path("navigation/", navigation_list, name="site-navigation"), path("footer/", footer_detail, name="site-footer"), path("contact/", contact_message_create, name="site-contact")]
