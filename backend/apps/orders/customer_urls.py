from django.urls import path

from . import api

urlpatterns = [
    path("orders/", api.customer_orders),
    path("orders/<int:order_id>/", api.customer_order_detail),
    path("orders/<int:order_id>/invoice/", api.invoice_download),
    path("orders/<int:order_id>/invoice/send/", api.invoice_send),
    path("orders/<int:order_id>/proforma/request/", api.proforma_request),
]
