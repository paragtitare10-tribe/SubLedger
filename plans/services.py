from .repositories import PlanRepository


class PlanService:
    @staticmethod
    def create(data):
        return PlanRepository.create(data)

    @staticmethod
    def update(plan, data):
        return PlanRepository.update(plan, data)

    @staticmethod
    def delete(plan):
        PlanRepository.delete(plan)