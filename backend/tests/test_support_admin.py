from django.contrib.auth import get_user_model
from django.test import TestCase
from apps.website.models import CustomerFeedback, CustomerSupportRequest, WarrantyPolicy, WarrantyRegistration

class SupportAdminTests(TestCase):
 def setUp(self):
  self.user=get_user_model().objects.create_superuser('admin','admin@example.com','x')
  self.client.force_login(self.user)
 def test_support_changelists_render(self):
  for model in (WarrantyPolicy, WarrantyRegistration, CustomerSupportRequest, CustomerFeedback):
   self.assertEqual(self.client.get(f'/admin/website/{model._meta.model_name}/').status_code,200)
 def test_null_context_records_render(self):
  WarrantyRegistration.objects.create(full_name='Anonymous',phone='09120000001')
  CustomerSupportRequest.objects.create(full_name='Anonymous',phone='09120000001',subject='Subject',message='Message')
  self.assertEqual(self.client.get('/admin/website/warrantyregistration/').status_code,200)
  self.assertEqual(self.client.get('/admin/website/customersupportrequest/').status_code,200)
