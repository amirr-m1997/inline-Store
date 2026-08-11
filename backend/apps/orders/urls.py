from django.urls import path

from . import api

urlpatterns = [
    path("payments/<int:payment_id>/", api.payment_detail),
    path("payments/<int:payment_id>/mock-complete/", api.mock_complete),
]
