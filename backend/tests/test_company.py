from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.company.models import CompanyBanner, CompanyInfo
from apps.website.models import ContactMessage, FooterLink, FooterSection, SiteNavigation, TrustBadge


class CompanyApiTests(TestCase):
    def test_hero_returns_active_banners_in_order(self):
        company = CompanyInfo.objects.order_by("id").first() or CompanyInfo.objects.create(name_fa="شرکت آزمایشی")
        image = SimpleUploadedFile("hero.jpg", b"image", content_type="image/jpeg")
        CompanyBanner.objects.create(company_info=company, desktop_image=image, title_fa="دوم", order=2)
        CompanyBanner.objects.create(company_info=company, desktop_image=SimpleUploadedFile("hero-1.jpg", b"image", content_type="image/jpeg"), title_fa="اول", order=1)
        CompanyBanner.objects.create(company_info=company, desktop_image=SimpleUploadedFile("hero-off.jpg", b"image", content_type="image/jpeg"), title_fa="خاموش", order=0, is_active=False)
        response = self.client.get("/api/v1/site/hero/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["title"] for item in response.json()["banners"]], ["اول", "دوم"])

    def test_contact_navigation_links_point_to_the_real_page(self):
        SiteNavigation.objects.create(title_fa="تماس با ما", url="/fa/contact")
        section = FooterSection.objects.create(title_fa="شرکت")
        FooterLink.objects.create(section=section, title_fa="تماس با ما", url="/fa/contact")
        navigation = self.client.get("/api/v1/site/navigation/").json()
        footer = self.client.get("/api/v1/site/footer/").json()
        self.assertIn("/fa/contact", [item["url"] for item in navigation])
        self.assertIn("/fa/contact", [link["url"] for item in footer["sections"] for link in item["links"]])
    def test_company_information_is_available(self):
        response = self.client.get("/api/v1/company/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name_fa"], "شرکت تولیدی مهر اصل")

    def test_footer_is_aggregated_and_excludes_inactive_links(self):
        section = FooterSection.objects.create(title_fa="آزمایش", order=1)
        FooterLink.objects.create(section=section, title_fa="فعال", url="/fa", is_active=True)
        FooterLink.objects.create(section=section, title_fa="غیرفعال", url="/hidden", is_active=False)

        response = self.client.get("/api/v1/site/footer/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        test_section = next(item for item in payload["sections"] if item["title"] == "آزمایش")
        self.assertEqual([item["title"] for item in test_section["links"]], ["فعال"])
        self.assertEqual(payload["company"]["name_fa"], "شرکت تولیدی مهر اصل")
        self.assertTrue(payload["copyright"])

    def test_footer_omits_badges_without_an_uploaded_image(self):
        TrustBadge.objects.create(title_fa="بدون تصویر")

        response = self.client.get("/api/v1/site/footer/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["trust_badges"], [])

    def test_contact_message_is_validated_and_stored(self):
        response = self.client.post("/api/v1/site/contact/", {
            "full_name": "مشتری آزمایشی", "phone": "09123456789",
            "email": "customer@example.com", "subject": "درخواست خرید", "message": "لطفاً تماس بگیرید.",
        }, content_type="application/json")

        self.assertEqual(response.status_code, 201)
        self.assertTrue(ContactMessage.objects.filter(phone="09123456789", status=ContactMessage.Status.NEW).exists())

    def test_contact_message_rejects_invalid_phone(self):
        response = self.client.post("/api/v1/site/contact/", {
            "full_name": "مشتری آزمایشی", "phone": "123",
            "subject": "درخواست خرید", "message": "پیام",
        }, content_type="application/json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ContactMessage.objects.count(), 0)
