import calendar
from datetime import date

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from customers.models import Customer
from plans.models import Plan

from .models import Subscription
from .repositories import SubscriptionRepository


def _add_months(value, months):
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


class SubscriptionService:
    @staticmethod
    @transaction.atomic
    def create(data):
        data = data.copy()
        customer = SubscriptionRepository.get_customer(data.pop('customer_id'))
        plan = SubscriptionRepository.get_plan(data.pop('plan_id'))
        if customer.status != Customer.Status.ACTIVE:
            raise ValidationError({'customer_id': 'An inactive customer cannot subscribe.'})
        if plan.status != Plan.Status.ACTIVE:
            raise ValidationError({'plan_id': 'An inactive plan cannot be subscribed to.'})

        start_date = data.pop('start_date', timezone.localdate())
        period_start = data.pop('current_period_start', start_date)
        period_end = data.pop('current_period_end', None)
        if period_end is None:
            cycle_months = {
                Plan.BillingCycle.MONTHLY: 1,
                Plan.BillingCycle.QUARTERLY: 3,
                Plan.BillingCycle.YEARLY: 12,
            }.get(plan.billing_cycle)
            if cycle_months is None:
                raise ValidationError({'current_period_end': 'Provide a period end for a custom billing cycle.'})
            period_end = _add_months(period_start, cycle_months)

        try:
            return SubscriptionRepository.create({
                'customer': customer,
                'plan': plan,
                'status': Subscription.Status.ACTIVE,
                'start_date': start_date,
                'current_period_start': period_start,
                'current_period_end': period_end,
            })
        except IntegrityError as error:
            raise ValidationError('This customer already has an active subscription to this plan.') from error

    @staticmethod
    @transaction.atomic
    def cancel(subscription):
        if subscription.status == Subscription.Status.CANCELED:
            return subscription
        return SubscriptionRepository.save(
            subscription,
            status=Subscription.Status.CANCELED,
            canceled_at=timezone.now(),
        )