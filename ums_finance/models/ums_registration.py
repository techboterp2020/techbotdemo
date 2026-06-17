from odoo import models


class UmsRegistration(models.Model):
    """Recompute tuition when registrations change (add/drop) — FR-FIN-02."""
    _inherit = 'ums.registration'

    def _notify_finance_recompute(self):
        # Hook other modules (instalments, scholarships) can extend; keeps the
        # student's financial hold in sync with the latest balance.
        self.mapped('student_id').sync_financial_hold()

    def action_drop(self):
        res = super().action_drop()
        self._notify_finance_recompute()
        return res

    def action_withdraw(self):
        res = super().action_withdraw()
        self._notify_finance_recompute()
        return res
