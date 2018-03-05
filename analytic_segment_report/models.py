from openerp import tools, models, fields, api
from openerp.tools.translate import _

class AccountReportGeneralLedgerWizard(models.TransientModel):

    _inherit = "general.ledger.webkit"

    analytic_segment_ids = fields.One2many('general.ledger.webkit.segments', 'report_id')


class AccountReportGeneralLedgerWizardSegments(models.TransientModel):

    _name = "general.ledger.webkit.segments"

    report_id = fields.Many2one('general.ledger.webkit')
    segment_id = fields.Many2one('analytic_segment.segment') #, required=True)
    segment = fields.Char(related='segment_id.segment', readonly=True)
    with_children = fields.Boolean(default=False)
