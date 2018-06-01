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


'''class AccountBalanceReportingLine(models.Model):

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
        return True'''
from openerp.osv import orm, fields
import re
class AccountBalanceReportingLine(orm.Model):

    _inherit = "account.balance.reporting.line"

    def refresh_values(self, cr, uid, ids, context=None):
        """Recalculates the values of this report line using the
        linked line report values formulas:

        Depending on this formula the final value is calculated as follows:
        - Empy report value: sum of (this concept) children values.
        - Number with decimal point ("10.2"): that value (constant).
        - Account numbers separated by commas ("430,431,(437)"): Sum of the
            account balances.
            (The sign of the balance depends on the balance mode)
        - Concept codes separated by "+" ("11000+12000"): Sum of those
            concepts values.
        """
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            tmpl_line = line.template_line_id
            balance_mode = int(tmpl_line.template_id.balance_mode)
            current_value = 0.0
            previous_value = 0.0
            report = line.report_id
            segment_ids = []
            for s in report.analytic_segment_ids
                segment_ids.append(s.segment_id.id)
                if s.with_children:
                    segment_ids += s.segment_id.segment_tmpl_id.get_childs_ids()
            print segment_ids
            # We use the same code to calculate both fiscal year values,
            # just iterating over them.
            for fyear in ('current', 'previous'):
                value = 0
                if fyear == 'current':
                    tmpl_value = tmpl_line.current_value
                elif fyear == 'previous':
                    tmpl_value = (tmpl_line.previous_value or
                                  tmpl_line.current_value)
                # Remove characters after a ";" (we use ; for comments)
                if tmpl_value:
                    tmpl_value = tmpl_value.split(';')[0]
                if (fyear == 'current' and not report.current_fiscalyear_id) \
                        or (fyear == 'previous' and
                            not report.previous_fiscalyear_id):
                    value = 0
                else:
                    if not tmpl_value:
                        # Empy template value => sum of the children values
                        for child in line.child_ids:
                            if child.calc_date != child.report_id.calc_date:
                                # Tell the child to refresh its values
                                child.refresh_values()
                                # Reload the child data
                                child = self.browse(cr, uid, child.id,
                                                    context=context)
                            if fyear == 'current':
                                value += child.current_value
                            elif fyear == 'previous':
                                value += child.previous_value
                    elif re.match(r'^\-?[0-9]*\.[0-9]*$', tmpl_value):
                        # Number with decimal points => that number value
                        # (constant).
                        value = float(tmpl_value)
                    elif re.match(r'^[0-9a-zA-Z,\(\)\*_\ ]*$', tmpl_value):
                        # Account numbers separated by commas => sum of the
                        # account balances. We will use the context to filter
                        # the accounts by fiscalyear and periods.
                        ctx = context.copy()
                        if fyear == 'current':
                            ctx.update({
                                'fiscalyear': report.current_fiscalyear_id.id,
                                'periods': [p.id for p in
                                            report.current_period_ids],
                                # 'segment_ids': [s.segment_id.id for s in report.analytic_segment_ids],
                                'segment_ids': segment_ids,
                            })
                        elif fyear == 'previous':
                            ctx.update({
                                'fiscalyear': report.previous_fiscalyear_id.id,
                                'periods': [p.id for p in
                                            report.previous_period_ids],
                                # 'segment_ids': [s.segment_id.id for s in report.analytic_segment_ids],
                                'segment_ids': segment_ids,
                            })
                        value = self._get_account_balance(
                            cr, uid, [line.id], tmpl_value,
                            balance_mode=balance_mode, context=ctx)
                    elif re.match(r'^[\+\-0-9a-zA-Z_\*\ ]*$', tmpl_value):
                        # Account concept codes separated by "+" => sum of the
                        # concepts (template lines) values.
                        for line_code in re.findall(r'(-?\(?[0-9a-zA-Z_]*\)?)',
                                                    tmpl_value):
                            sign = 1
                            if (line_code.startswith('-') or
                                    (line_code.startswith('(') and
                                     balance_mode in (2, 4))):
                                sign = -1
                            line_code = line_code.strip('-()*')
                            # findall might return empty strings
                            if line_code:
                                # Search for the line (perfect match)
                                line_ids = self.search(cr, uid, [
                                    ('report_id', '=', report.id),
                                    ('code', '=', line_code),
                                ], context=context)
                                for child in self.browse(cr, uid, line_ids,
                                                         context=context):
                                    if (child.calc_date !=
                                            child.report_id.calc_date):
                                        child.refresh_values()
                                        # Reload the child data
                                        child = self.browse(cr, uid, child.id,
                                                            context=context)
                                    if fyear == 'current':
                                        value += child.current_value * sign
                                    elif fyear == 'previous':
                                        value += child.previous_value * sign
                # Negate the value if needed
                if tmpl_line.negate:
                    value = -value
                if fyear == 'current':
                    current_value = value
                elif fyear == 'previous':
                    previous_value = value
            # Write the values
            self.write(cr, uid, line.id, {
                'current_value': current_value,
                'previous_value': previous_value,
                'calc_date': line.report_id.calc_date,
            }, context=context)
        return True


