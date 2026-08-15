from django.urls import path

from .api import capability_detail, capability_list, company_certifications, company_detail, company_honors, company_locations, company_milestones, company_sections, industry_detail, industry_list

urlpatterns = [path("", company_detail, name="company-detail"), path("sections/", company_sections, name="company-sections"), path("capabilities/", capability_list, name="capability-list"), path("capabilities/<slug:slug>/", capability_detail, name="capability-detail"), path("locations/", company_locations, name="company-locations"), path("milestones/", company_milestones, name="company-milestones"), path("certifications/", company_certifications, name="company-certifications"), path("honors/", company_honors, name="company-honors"), path("industries/", industry_list, name="industry-list"), path("industries/<slug:slug>/", industry_detail, name="industry-detail")]
