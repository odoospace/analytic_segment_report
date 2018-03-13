from openerp import tools, models, fields, api
from openerp.tools.translate import _

class AccountBlanaceReportingSegments(models.Model):

    _name = "account.balance.reporting.segments"

    def _domain_segment(self):
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


    report_id = fields.Many2one('account.balance.reporting')
    segment_id = fields.Many2one('analytic_segment.segment', domain=_domain_segment) #, required=True)
    segment = fields.Char(related='segment_id.segment', readonly=True)
    with_children = fields.Boolean(default=False)

class AccountBalanceReporting(models.Model):

    _inherit = "account.balance.reporting"

    analytic_segment_ids = fields.One2many(
        'account.balance.reporting.segments', 
        'report_id',
        states={'calc_done': [('readonly', True)],
                'done': [('readonly', True)]})


class AccountBalanceReportingLine(models.Model):

    _inherit = "account.balance.reporting.line"


    @api.multi
    def refresh_values(self):
        #account_balance_reporting override for segment domain
        for report in self.mapped('report_id'):
            domain_current = []
            #add segments
            segment_ids = []
            for segment in report.analytic_segment_ids:
                segment_ids += [segment.segment_id.id]
                if segment.with_children:
                    segment_ids += segment.segment_id.segment_tmpl_id.get_childs_ids()
            # Compute current fiscal year
            if report.check_filter == 'dates':
                domain_current += [('date', '>=', report.current_date_from),
                                   ('date', '<=', report.current_date_to),
                                   ('segment_id', 'in', segment_ids)]
            elif report.check_filter == 'periods':
                if report.current_period_ids:
                    periods = report.current_period_ids
                else:
                    periods = report.current_fiscalyear_id.period_ids
                domain_current += [('period_id', 'in', periods.ids),
                                   ('segment_id', 'in', segment_ids)]
            # Compute previous fiscal year
            domain_previous = []
            if report.check_filter == 'dates':
                domain_previous += [('date', '>=', report.previous_date_from),
                                    ('date', '<=', report.previous_date_to),
                                   ('segment_id', 'in', segment_ids)]
            elif report.check_filter == 'periods':
                if report.previous_period_ids:
                    periods = report.previous_period_ids
                else:
                    periods = report.previous_fiscalyear_id.period_ids
                domain_previous += [('period_id', 'in', periods.ids),
                                   ('segment_id', 'in', segment_ids)]
            for line in self.filtered(lambda l: l.report_id == report):
                if (line.calc_date and
                        line.calc_date == line.report_id.calc_date):
                    continue
                current_amount, current_move_lines = line._calculate_value(
                    domain_current, 'current')
                previous_amount, previous_move_lines = line._calculate_value(
                    domain_previous, 'previous')
                line.write({
                    'current_value': current_amount,
                    'previous_value': previous_amount,
                    'calc_date': line.report_id.calc_date,
                    'current_move_line_ids': [(6, 0, current_move_lines.ids)],
                    'previous_move_line_ids': [
                        (6, 0, previous_move_lines.ids)],
                })
                # HACK: For assuring the values got updated on call loop
                line.refresh()
        return True


