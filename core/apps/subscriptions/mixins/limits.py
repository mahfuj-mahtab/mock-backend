from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.mock_prep.models import InterviewSession, SessionStatus
from apps.subscriptions.models import SubscriptionPlan


class SubscriptionLimitMixin:
    def get_plan(self, user) -> SubscriptionPlan:
        if user.plan_id:
            return user.plan
        plan = SubscriptionPlan.objects.filter(is_default=True).first()
        if plan is None:
            raise ValidationError({"detail": ["No subscription plan is configured."]})
        user.plan = plan
        user.save(update_fields=["plan"])
        return plan

    def _used_this_month(self, user) -> int:
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return InterviewSession.objects.filter(
            user=user,
            started_at__gte=month_start,
            status__in=[
                SessionStatus.ACTIVE,
                SessionStatus.COMPLETED,
                SessionStatus.ABANDONED,
            ],
        ).count()

    def enforce_subscription_limit(self, user) -> SubscriptionPlan:
        plan = self.get_plan(user)
        limit = plan.monthly_session_limit
        if limit is not None and self._used_this_month(user) >= limit:
            raise ValidationError(
                {
                    "detail": [
                        f"Your {plan.name} plan includes {limit} mock interviews per month."
                    ]
                }
            )
        return plan

    def apply_subscription_limits(self, session: InterviewSession) -> InterviewSession:
        plan = self.get_plan(session.user)
        session.duration_minutes = plan.duration_minutes
        session.target_question_count = plan.question_count
        session.max_followups = plan.max_followups
        session.max_followups_per_question = plan.max_followups_per_question
        session.save(
            update_fields=[
                "duration_minutes",
                "target_question_count",
                "max_followups",
                "max_followups_per_question",
            ]
        )
        return session

    def subscription_usage(self, user) -> dict:
        plan = self.get_plan(user)
        used = self._used_this_month(user)
        limit = plan.monthly_session_limit
        return {
            "plan": plan.slug,
            "plan_name": plan.name,
            "limit": limit,
            "used": used,
            "remaining": None if limit is None else max(0, limit - used),
            "duration_minutes": plan.duration_minutes,
            "question_count": plan.question_count,
            "max_followups": plan.max_followups,
            "max_followups_per_question": plan.max_followups_per_question,
        }
