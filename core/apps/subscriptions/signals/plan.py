from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.subscriptions.models import SubscriptionPlan


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def assign_default_plan(sender, instance, created, **kwargs):
    if not created or instance.plan_id:
        return
    plan = SubscriptionPlan.objects.filter(is_default=True).first()
    if plan is None:
        return
    instance.plan = plan
    instance.save(update_fields=["plan"])
