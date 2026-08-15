from django.db import migrations, models


def published_review_state_to_ready(apps, schema_editor):
    for model_name in ("ContentArticle", "FAQEntry"):
        model = apps.get_model("content", model_name)
        model.objects.filter(review_status="published").update(review_status="ready")


class Migration(migrations.Migration):
    dependencies = [("content", "0004_contentarticle_review_status_and_more")]

    operations = [
        migrations.RunPython(published_review_state_to_ready, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="contentarticle",
            name="review_status",
            field=models.CharField(choices=[("draft", "پیش‌نویس"), ("needs_review", "نیازمند بررسی"), ("ready", "آماده انتشار")], db_index=True, default="draft", max_length=20),
        ),
        migrations.AlterField(
            model_name="faqentry",
            name="review_status",
            field=models.CharField(choices=[("draft", "پیش‌نویس"), ("needs_review", "نیازمند بررسی"), ("ready", "آماده انتشار")], db_index=True, default="draft", max_length=20),
        ),
    ]
