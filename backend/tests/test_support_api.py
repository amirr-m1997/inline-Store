from django.test import TestCase
from rest_framework.test import APIClient
from apps.website.models import WarrantyPolicy

class SupportApiTests(TestCase):
 def setUp(self): self.client=APIClient()
 def test_policy_is_published_only(self):
  WarrantyPolicy.objects.create(title_fa="draft", is_published=False); WarrantyPolicy.objects.create(title_fa="published", is_published=True)
  self.assertEqual(self.client.get('/api/v1/site/support/warranty-policy/').json()['title_fa'], 'published')
 def test_invalid_and_anonymous_submissions(self):
  self.assertEqual(self.client.post('/api/v1/site/support/requests/', {'full_name':'x','phone':'bad','subject':'x','message':'x'}, format='json').status_code,400)
  response=self.client.post('/api/v1/site/support/requests/', {'full_name':'x','phone':'09120000001','subject':'x','message':'x','product':999999}, format='json')
  self.assertEqual(response.status_code,400)
  response=self.client.post('/api/v1/site/support/requests/', {'full_name':'x','phone':'09120000001','subject':'x','message':'x'}, format='json')
  self.assertEqual(response.status_code,201); self.assertTrue(response.json()['reference'].startswith('SUP-')); self.assertNotIn('customer',response.json())
 def test_feedback_validation(self):
  self.assertEqual(self.client.post('/api/v1/site/support/feedback/', {'message':'x','rating':6}, format='json').status_code,400)
  self.assertEqual(self.client.post('/api/v1/site/support/feedback/', {'message':'x','rating':5}, format='json').status_code,201)
