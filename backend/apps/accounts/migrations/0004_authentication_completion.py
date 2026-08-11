import re
import django.db.models.deletion
from django.db import migrations, models


def normalize_identities(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    emails, phones = set(), set()
    for user in User.objects.order_by("id"):
        email = (user.email or "").strip().lower() or None
        if email in emails: email = None
        if email: emails.add(email)
        raw = re.sub(r"[\s\-()]", "", user.phone or "")
        if raw.startswith("0098"): phone = "+98" + raw[4:]
        elif raw.startswith("98"): phone = "+" + raw
        elif raw.startswith("0"): phone = "+98" + raw[1:]
        else: phone = raw or None
        if not phone or not re.fullmatch(r"\+989\d{9}", phone) or phone in phones: phone = None
        if phone: phones.add(phone)
        User.objects.filter(pk=user.pk).update(email=email, phone=phone)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_user_customer_fields")]
    operations = [
        migrations.AlterField(model_name="user", name="email", field=models.EmailField(blank=True, max_length=254, null=True, unique=True)),
        migrations.AlterField(model_name="user", name="phone", field=models.CharField(blank=True, max_length=32, null=True)),
        migrations.RunPython(normalize_identities, migrations.RunPython.noop),
        migrations.AlterField(model_name="user", name="phone", field=models.CharField(blank=True, max_length=16, null=True, unique=True)),
        migrations.CreateModel(name="PhoneOTP", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("phone", models.CharField(db_index=True, max_length=16)), ("purpose", models.CharField(choices=[("login", "ورود"), ("password_reset", "بازیابی رمز")], max_length=20)), ("code_hash", models.CharField(max_length=128)), ("expires_at", models.DateTimeField()), ("attempts", models.PositiveSmallIntegerField(default=0)), ("max_attempts", models.PositiveSmallIntegerField(default=5)), ("consumed_at", models.DateTimeField(blank=True, null=True)), ("created_at", models.DateTimeField(auto_now_add=True))], options={"ordering": ("-created_at",), "verbose_name": "کد یکبار مصرف", "verbose_name_plural": "کدهای یکبار مصرف"}),
        migrations.CreateModel(name="GoogleIdentity", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("subject", models.CharField(max_length=255, unique=True)), ("created_at", models.DateTimeField(auto_now_add=True)), ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="google_identity", to="accounts.user"))], options={"verbose_name": "هویت گوگل", "verbose_name_plural": "هویت‌های گوگل"}),
    ]
