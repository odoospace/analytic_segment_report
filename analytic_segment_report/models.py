from openerp import tools, models, fields, api
from openerp.tools.translate import _
import json

#General Ledger - libro mayor
class AccountReportGeneralLedgerWizard(models.TransientModel):

    _inherit = "general.ledger.webkit"

    analytic_segment_ids = fields.One2many('general.ledger.webkit.segments', 'report_id')


class AccountReportGeneralLedgerWizardSegments(models.TransientModel):

    _name = "general.ledger.webkit.segments"

    def _domain_segment(self):
        if self.env.user.id == 1:
            domain = []
        else:
            segment_by_company_open = json.loads(self.env.user.segment_by_company_open)[str(self.env.user.company_id.id)]
            domain = [('id', 'in', segment_by_company_open)]
        return domain


    report_id = fields.Many2one('general.ledger.webkit')
    segment_id = fields.Many2one('analytic_segment.segment', domain=_domain_segment) #, required=True)
    segment = fields.Char(related='segment_id.segment', readonly=True)
    with_children = fields.Boolean(default=False)

#Trial balance - sumas y saldos
class AccountTrialBalanceWizard(models.TransientModel):

    _inherit = "trial.balance.webkit"

    analytic_segment_ids = fields.One2many('trial.balance.webkit.segments', 'report_id')


class AccountReportTrialBalanceWizardSegments(models.TransientModel):

    _name = "trial.balance.webkit.segments"

    def _domain_segment(self):
        if self.env.user.id == 1:
            domain = []
            return domain
        else:
            return [('id', 'in', [i.id for i in self.env.user.segment_segment_ids])]

    report_id = fields.Many2one('trial.balance.webkit')
    segment_id = fields.Many2one('analytic_segment.segment', domain=_domain_segment) #, required=True)
    segment = fields.Char(related='segment_id.segment', readonly=True)
    with_children = fields.Boolean(default=False)

