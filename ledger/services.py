from .repositories import LedgerRepository


class LedgerService:
    @staticmethod
    def list_entries():
        return LedgerRepository.list()

    @staticmethod
    def record_invoice_created(invoice, subscription_id):
        return LedgerRepository.create_entry(
            customer=invoice.customer,
            invoice=invoice,
            entry_type='charge',
            amount=invoice.amount_due,
            currency=invoice.currency,
            reference_id=f'invoice:{invoice.id}',
            description=f'Invoice charge for subscription {subscription_id}',
        )