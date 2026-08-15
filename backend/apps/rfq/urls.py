from django.urls import path

from .api import rfq_cart_context, rfq_collection, rfq_detail, quotation_collection, quotation_detail, quotation_pdf, quotation_respond

urlpatterns = [
    path("", rfq_collection, name="rfq-collection"),
    path("cart-context/", rfq_cart_context, name="rfq-cart-context"),
    path("quotations/", quotation_collection, name="quotation-collection"),
    path("quotations/<str:reference>/pdf/", quotation_pdf, name="quotation-pdf"),
    path("quotations/<str:reference>/respond/", quotation_respond, name="quotation-respond"),
    path("quotations/<str:reference>/", quotation_detail, name="quotation-detail"),
    path("<str:reference>/", rfq_detail, name="rfq-detail"),
]
