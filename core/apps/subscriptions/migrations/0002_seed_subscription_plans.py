from django.db import migrations


PLAN_ROWS = [
    {
        "name": "Free",
        "slug": "free",
        "description": "3 short mocks each month.",
        "is_default": True,
        "is_active": True,
        "monthly_session_limit": 3,
        "duration_minutes": 15,
        "question_count": 5,
        "max_followups": 5,
        "max_followups_per_question": 1,
        "sort_order": 0,
    },
    {
        "name": "Starter",
        "slug": "starter",
        "description": "More mocks and a longer session.",
        "is_default": False,
        "is_active": True,
        "monthly_session_limit": 10,
        "duration_minutes": 25,
        "question_count": 8,
        "max_followups": 8,
        "max_followups_per_question": 1,
        "sort_order": 1,
    },
    {
        "name": "Pro",
        "slug": "pro",
        "description": "Unlimited monthly mocks with a full session.",
        "is_default": False,
        "is_active": True,
        "monthly_session_limit": None,
        "duration_minutes": 40,
        "question_count": 15,
        "max_followups": 15,
        "max_followups_per_question": 1,
        "sort_order": 2,
    },
]


def seed_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model("subscriptions", "SubscriptionPlan")
    User = apps.get_model("accounts", "User")
    UserSubscription = apps.get_model("subscriptions", "UserSubscription")

    for row in PLAN_ROWS:
        SubscriptionPlan.objects.update_or_create(slug=row["slug"], defaults=row)

    free = SubscriptionPlan.objects.get(slug="free")
    existing_user_ids = UserSubscription.objects.filter(status="active").values_list(
        "user_id",
        flat=True,
    )
    for user in User.objects.exclude(id__in=existing_user_ids):
        UserSubscription.objects.create(user=user, plan=free, status="active")


def unseed_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model("subscriptions", "SubscriptionPlan")
    SubscriptionPlan.objects.filter(slug__in=["free", "starter", "pro"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptions", "0001_subscription_plans"),
        ("accounts", "0002_socialaccount"),
    ]

    operations = [
        migrations.RunPython(seed_plans, unseed_plans),
    ]
