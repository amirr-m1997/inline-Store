from django.urls import path

from .api import contact_message_create, feedback_create, footer_detail, navigation_list, support_requests, warranty_policy, warranty_registrations

urlpatterns = [path("navigation/", navigation_list, name="site-navigation"), path("footer/", footer_detail, name="site-footer"), path("contact/", contact_message_create, name="site-contact"), path("support/warranty-policy/", warranty_policy), path("support/warranty-registrations/", warranty_registrations), path("support/requests/", support_requests), path("support/feedback/", feedback_create)]
