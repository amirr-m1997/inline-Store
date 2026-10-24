from django.apps import apps
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save

from .audit import should_track, snapshot, write_event


def capture_before_save(sender, instance, **kwargs):
    if not should_track(sender) or not instance.pk:
        instance._audit_before = None
        return
    previous = sender._default_manager.filter(pk=instance.pk).first()
    instance._audit_before = snapshot(previous) if previous else None


def capture_after_save(sender, instance, created, raw=False, **kwargs):
    if raw or not should_track(sender):
        return
    current = snapshot(instance)
    if created:
        write_event(instance, "create", {"after": current})
        return
    before = getattr(instance, "_audit_before", None)
    if before is None:
        return
    changed = {
        key: {"before": before[key], "after": current[key]}
        for key in current
        if before.get(key) != current.get(key)
    }
    if changed:
        write_event(instance, "update", changed)


def capture_before_delete(sender, instance, **kwargs):
    if should_track(sender):
        instance._audit_before_delete = snapshot(instance)


def capture_after_delete(sender, instance, **kwargs):
    if should_track(sender):
        write_event(instance, "delete", {"before": getattr(instance, "_audit_before_delete", snapshot(instance))})


def connect_audit_signals():
    for model in apps.get_models():
        if not should_track(model):
            continue
        key = model._meta.label_lower
        pre_save.connect(capture_before_save, sender=model, dispatch_uid=f"audit-pre-save:{key}")
        post_save.connect(capture_after_save, sender=model, dispatch_uid=f"audit-post-save:{key}")
        pre_delete.connect(capture_before_delete, sender=model, dispatch_uid=f"audit-pre-delete:{key}")
        post_delete.connect(capture_after_delete, sender=model, dispatch_uid=f"audit-post-delete:{key}")
