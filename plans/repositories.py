from .models import Plan


class PlanRepository:
    @staticmethod
    def list():
        return Plan.objects.all()

    @staticmethod
    def get(plan_id):
        return Plan.objects.get(pk=plan_id)

    @staticmethod
    def exists(plan_id):
        return Plan.objects.filter(pk=plan_id).exists()

    @staticmethod
    def create(data):
        return Plan.objects.create(**data)

    @staticmethod
    def update(plan, data):
        for field, value in data.items():
            setattr(plan, field, value)
        plan.save()
        return plan

    @staticmethod
    def delete(plan):
        plan.delete()