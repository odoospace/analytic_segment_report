from openerp import tools, models, fields, api
from openerp.tools.translate import _

#General Ledger - libro mayor
class AccountReportGeneralLedgerWizard(models.TransientModel):

    _inherit = "general.ledger.webkit"

    analytic_segment_ids = fields.One2many('general.ledger.webkit.segments', 'report_id')


class AccountReportGeneralLedgerWizardSegments(models.TransientModel):

    _name = "general.ledger.webkit.segments"

    def _domain_segment(self):
        # TODO: refactor these 3 functions!!!!
        if self.env.user.id == 1:
            # no restrictions
            domain = []
        else:
            segment_tmpl_ids = []
            segment_ids = self.env.user.segment_ids
            for s in segment_ids:
                segment_tmpl_ids += [s.segment_id.segment_tmpl_id.id]
                segment_tmpl_ids += s.segment_id.segment_tmpl_id.get_childs_ids()
            virtual_segments = self.env['analytic_segment.template'].search([('virtual', '=', True)])
            segment_tmpl_ids += [i.id for i in virtual_segments]

            segment_ids = self.env['analytic_segment.segment'].search([('segment_tmpl_id', 'in', segment_tmpl_ids)])
            domain = [('id', 'in', [i.id for i in segment_ids])]
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

    report_id = fields.Many2one('trial.balance.webkit')
    segment_id = fields.Many2one('analytic_segment.segment') #, required=True)
    segment = fields.Char(related='segment_id.segment', readonly=True)
    with_children = fields.Boolean(default=False)

