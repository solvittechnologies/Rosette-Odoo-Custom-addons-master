from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
import base64
from io import BytesIO

Months = [('January', 'January'),
          ('february', 'February'),
          ('march', 'March'),
          ('april', 'April'),
          ('may', 'May'),
          ('june', 'June'),
          ('july', 'July'),
          ('august', 'August'),
          ('september', 'September'),
          ('october', 'October'),
          ('november', 'November'),
          ('december', 'December')]

Payroll_Type_Selection = [('basic_salary', 'Basic Salary'),
                          ('transport_allowance', 'Transport Allowance'),
                          ('utilities_allowance', 'Utilities Allowance'),
                          ('house_Rent_Allowance', 'House Rent Allowance'),
                          ('employee_benefit_gratuity_loan', 'Employee Benefit/Gratuity/Loan'),
                          ('overtime_odp', 'OVERTIME/ODP'),
                          ('monthly_gross_pay', 'Monthly Gross Pay'),
                          ('total_monthly_gross_pay', 'Total Monthly Gross Pay'),
                          ('paye', 'PAYE'),
                          ('advance_salary', 'ADVANCE SALARY'),
                          ('nhf', 'NHF'),
                          ('pension', 'PENSION'),
                          ('loan_repayment', 'LOAN REPAYMENT'),
                          ('absent_odp_penalty', 'ABSENT/ODP/PENALTY'),
                          ('total_deductions', 'TOTAL DEDUCTIONS'),
                          ('net_pay', 'NET PAY')]


class HRPayslipCustom(models.Model):
    _name = 'hr.payslip.custom'

    name = fields.Char("Payslip Name")
    state = fields.Selection([('draft', 'Draft'), ('validated', 'Validated')], string="State", default='draft')
    location_id = fields.Many2one('stock.location', "Location")
    date_from = fields.Date(string='Date From', required=True,
                            default=lambda self: fields.Date.to_string(date.today().replace(day=1)),
                            )
    date_to = fields.Date(string='Date To', required=True,
                          default=lambda self: fields.Date.to_string(
                              (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()),
                          )
    month = fields.Selection(Months, string="Month")
    employee_tag = fields.Char("Reference Number")
    account_analytic_id = fields.Many2one('account.analytic.account', "Analytic Account")
    payslip_custom_line_ids = fields.One2many('hr.payslip.custom.line', 'payslip_custom_id', string="Lines", copy=True)

    move_ids = fields.Many2many('account.move', 'hr_custom_move_rel', 'hr_custom_id', 'move_id', string="Moves", compute='get_move_ids')
    excel_file = fields.Binary('Excel File')
    file_name = fields.Char('File Name')
    payslip_custom_account_line_ids = fields.One2many('hr.payslip.custom.account.line', 'payslip_custom_id', string="Account Lines", copy=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)

    @api.multi
    @api.depends('payslip_custom_account_line_ids')
    def get_move_ids(self):
        for rec in self:
            move_ids_list = []
            for line in rec.payslip_custom_account_line_ids:
                if line.move_id:
                    move_ids_list.append(line.move_id.id)
            rec.move_ids = [(6, 0, move_ids_list)]

    @api.multi
    def action_validate(self):
        self.write({'state': 'validated'})

        vals = {'name': self.name,
                'location_id': self.location_id and self.location_id.id or False,
                'date_from': self.date_from,
                'date_to': self.date_to,
                'month': self.month,
                'account_analytic_id': self.account_analytic_id and self.account_analytic_id.id or False,
                'line_ids': []}
        for line in self.payslip_custom_line_ids:
            vals['line_ids'].append((0, 0, {'beneficiary_name': line.employe_name and line.employe_name.name or False,
                                            'payment_amount': line.net_pay,
                                            }))
        self.env['salaries.excel.sheet'].sudo().create(vals)
        return

    @api.multi
    def button_journal_entries(self):
        return {
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.move_ids.ids)],
        }

    def generate_excel(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)

        worksheet = workbook.add_worksheet('Payroll Report')

        bold = workbook.add_format({'bold': True})
        border = workbook.add_format({'border': 1})
        format1 = workbook.add_format({'bold': True, 'border': 1})

        row = 0
        worksheet.write(row, 0, 'Staff ID', format1)
        worksheet.write(row, 1, 'Account details', format1)
        worksheet.write(row, 2, 'Place of Designation', format1)
        worksheet.write(row, 3, 'Names of Employees', format1)
        worksheet.write(row, 4, 'Function', format1)
        worksheet.write(row, 5, 'Position', format1)
        worksheet.write(row, 6, 'Basic Salary', format1)
        worksheet.write(row, 7, 'Transport Allowance', format1)
        worksheet.write(row, 8, 'Utilities Allowance', format1)
        worksheet.write(row, 9, 'House Rent Allowance', format1)
        worksheet.write(row, 10, 'Employee Benefit/Gratuity/Loan', format1)
        worksheet.write(row, 11, 'OVERTIME/ODP', format1)
        worksheet.write(row, 12, 'Monthly Gross Pay', format1)
        worksheet.write(row, 13, 'Total Monthly Gross Pay', format1)
        worksheet.write(row, 14, 'PAYE', format1)
        worksheet.write(row, 15, 'ADVANCE SALARY', format1)
        worksheet.write(row, 16, 'NHF', format1)
        worksheet.write(row, 17, 'PENSION', format1)
        worksheet.write(row, 18, 'LOAN REPAYMENT', format1)
        worksheet.write(row, 19, 'ABSENT/ODP/PENALTY', format1)
        worksheet.write(row, 20, 'TOTAL DEDUCTIONS', format1)
        worksheet.write(row, 21, 'NET PAY', format1)
        worksheet.write(row, 22, 'Hourly Pay', format1)
        worksheet.write(row, 23, 'Hourly Worked', format1)
        worksheet.write(row, 24, 'Overtime', format1)
        worksheet.write(row, 25, 'Overtime Amount', format1)
        worksheet.write(row, 26, 'Days Worked', format1)
        worksheet.write(row, 27, 'Daily Pay', format1)
        worksheet.write(row, 28, 'Off Duty Working', format1)

        row += 1

        basic_salary = transport_allowance = utilities_allowance = house_rent_allowance = employee_benefit_gratuity_loan = overtime_odp = monthly_gross_pay = total_monthly_gross_pay = paye = 0.0
        advance_salary = nhf = pension = loan_repayment = absent_odp_penalty = total_deductions = net_pay = hourly_pay = hourly_worked = overtime = amount = days_worked = daily_pay = off_duty_working = 0.0

        for line in self.payslip_custom_line_ids:
            worksheet.write(row, 0, line.staff_id or '')
            worksheet.write(row, 1, line.payment_mode or '')
            worksheet.write(row, 2, line.designation_place or '')
            worksheet.write(row, 3, line.employe_name and line.employe_name.name or '')
            worksheet.write(row, 4, line.function and line.function.name or '')
            worksheet.write(row, 5, line.position and line.position.name or '')

            worksheet.write(row, 6, line.basic_salary or '')
            basic_salary += line.basic_salary
            worksheet.write(row, 7, line.transport_allowance or '')
            transport_allowance += line.transport_allowance

            worksheet.write(row, 8, line.utilities_allowance or '')
            utilities_allowance += line.utilities_allowance

            worksheet.write(row, 9, line.house_Rent_Allowance or '')
            house_rent_allowance += line.house_Rent_Allowance

            worksheet.write(row, 10, line.employee_benefit_gratuity_loan or '')
            employee_benefit_gratuity_loan += line.employee_benefit_gratuity_loan

            worksheet.write(row, 11, line.overtime_odp or '')
            overtime_odp += line.overtime_odp

            worksheet.write(row, 12, line.monthly_gross_pay or '')
            monthly_gross_pay += line.monthly_gross_pay

            worksheet.write(row, 13, line.total_monthly_gross_pay or '')
            total_monthly_gross_pay += line.total_monthly_gross_pay

            worksheet.write(row, 14, line.paye or '')
            paye += line.paye

            worksheet.write(row, 15, line.advance_salary or '')
            advance_salary += line.advance_salary

            worksheet.write(row, 16, line.nhf or '')
            nhf += line.nhf

            worksheet.write(row, 17, line.pension or '')
            pension += line.pension

            worksheet.write(row, 18, line.loan_repayment or '')
            loan_repayment += line.loan_repayment

            worksheet.write(row, 19, line.absent_odp_penalty or '')
            absent_odp_penalty += line.absent_odp_penalty

            worksheet.write(row, 20, line.total_deductions or '')
            total_deductions += line.total_deductions

            worksheet.write(row, 21, line.net_pay or '')
            net_pay += line.net_pay

            worksheet.write(row, 22, line.hourly_pay or '')
            hourly_pay += line.hourly_pay

            worksheet.write(row, 23, line.hourly_worked or '')
            hourly_worked += line.hourly_worked

            worksheet.write(row, 24, line.overtime or '')
            overtime += line.overtime

            worksheet.write(row, 25, line.amount or '')
            amount += line.amount

            worksheet.write(row, 26, line.days_worked or '')
            days_worked += line.days_worked

            worksheet.write(row, 27, line.daily_pay or '')
            daily_pay += line.daily_pay

            worksheet.write(row, 28, line.off_duty_working or '')
            off_duty_working += line.off_duty_working
            row += 1

        worksheet.write(row, 6, basic_salary, bold)
        worksheet.write(row, 7, transport_allowance, bold)
        worksheet.write(row, 8, utilities_allowance, bold)
        worksheet.write(row, 9, house_rent_allowance, bold)
        worksheet.write(row, 10, employee_benefit_gratuity_loan, bold)
        worksheet.write(row, 11, overtime_odp, bold)
        worksheet.write(row, 12, monthly_gross_pay, bold)
        worksheet.write(row, 13, total_monthly_gross_pay, bold)
        worksheet.write(row, 14, paye, bold)
        worksheet.write(row, 15, advance_salary, bold)
        worksheet.write(row, 16, nhf, bold)
        worksheet.write(row, 17, pension, bold)
        worksheet.write(row, 18, loan_repayment, bold)
        worksheet.write(row, 19, absent_odp_penalty, bold)
        worksheet.write(row, 20, total_deductions, bold)
        worksheet.write(row, 21, net_pay, bold)
        worksheet.write(row, 22, hourly_pay, bold)
        worksheet.write(row, 23, hourly_worked, bold)
        worksheet.write(row, 24, overtime, bold)
        worksheet.write(row, 25, amount, bold)
        worksheet.write(row, 26, days_worked, bold)
        worksheet.write(row, 27, daily_pay, bold)
        worksheet.write(row, 28, off_duty_working, bold)

        workbook.close()
        file_data.seek(0)
        self.write(
            {'excel_file': base64.encodebytes(file_data.read()),
             'file_name': 'Payroll.xlsx'})

        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=hr.payslip.custom&id=" + str(self.id) + "&filename_field=filename&field=excel_file&download=true&filename=" + self.file_name,
            'target': 'current'
        }


class HRPayslipCustomAccountLine(models.Model):
    _name = 'hr.payslip.custom.account.line'

    payslip_custom_id = fields.Many2one('hr.payslip.custom',string="Payslip Custom Id")
    account_debit = fields.Many2one('account.account', 'Debit Account', domain=[('deprecated', '=', False)])
    account_credit = fields.Many2one('account.account', 'Credit Account', domain=[('deprecated', '=', False)])
    journal_id = fields.Many2one('account.journal', string='Journal')
    payroll_type = fields.Selection(selection=Payroll_Type_Selection, string="Payroll Type")
    type_amount = fields.Float('Type Amount', compute='get_type_amount')
    line_ids = fields.Many2many('hr.payslip.custom.line', compute='get_line_ids')
    state = fields.Selection([('draft', 'Draft'),
                              ('post', 'Post')], string="Status")
    move_id = fields.Many2one('account.move', string="Move")

    @api.model
    def create(self, vals):
        res = super(HRPayslipCustomAccountLine, self).create(vals)
        if res and res.state == 'post':
            if not res.journal_id:
                raise UserError(_('Journal is not set!! Please Set Journal.'))
            if not res.account_credit or not res.account_debit:
                raise UserError(_('You need to set debit/credit account for validate.'))

            debit_vals = {
                'name': dict(res._fields['payroll_type'].selection).get(res.payroll_type),
                'debit': res.type_amount,
                'credit': 0.0,
                'account_id': res.account_debit.id,
            }
            credit_vals = {
                'name': dict(res._fields['payroll_type'].selection).get(res.payroll_type),
                'debit': 0.0,
                'credit': res.type_amount,
                'account_id': res.account_credit.id,
            }
            vals = {
                'journal_id': res.journal_id.id,
                'date': datetime.now().date(),
                'ref': res.payslip_custom_id.name,
                'state': 'draft',
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.action_post()
            res.write({'move_id': move.id})
        return res

    @api.multi
    def write(self, vals):
        res = super(HRPayslipCustomAccountLine, self).write(vals)
        if vals.get('state', False) and vals['state'] == 'post' and not self.move_id:
            if not self.journal_id:
                raise UserError(_('Journal is not set!! Please Set Journal.'))
            if not self.account_credit or not self.account_debit:
                raise UserError(_('You need to set debit/credit account for validate.'))

            debit_vals = {
                'name': dict(self._fields['payroll_type'].selection).get(self.payroll_type),
                'debit': self.type_amount,
                'credit': 0.0,
                'account_id': self.account_debit.id,
            }
            credit_vals = {
                'name': dict(self._fields['payroll_type'].selection).get(self.payroll_type),
                'debit': 0.0,
                'credit': self.type_amount,
                'account_id': self.account_credit.id,
            }
            vals = {
                'journal_id': self.journal_id.id,
                'date': datetime.now().date(),
                'ref': self.payslip_custom_id.name,
                'state': 'draft',
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.action_post()
            self.write({'move_id': move.id})
        if vals.get('state', False) and vals['state'] == 'post' and self.move_id:
            self.move_id.button_cancel()
            self.move_id.line_ids.unlink()
            debit_vals = {
                'name': dict(self._fields['payroll_type'].selection).get(self.payroll_type),
                'debit': self.type_amount,
                'credit': 0.0,
                'account_id': self.account_debit.id,
            }
            credit_vals = {
                'name': dict(self._fields['payroll_type'].selection).get(self.payroll_type),
                'debit': 0.0,
                'credit': self.type_amount,
                'account_id': self.account_credit.id,
            }
            self.move_id.write({'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]})
            self.move_id.action_post()
        return res


    @api.multi
    @api.depends('payslip_custom_id', 'payslip_custom_id.payslip_custom_line_ids')
    def get_line_ids(self):
        for rec in self:
            if rec.payslip_custom_id and rec.payslip_custom_id.payslip_custom_line_ids:
                rec.line_ids = [(6, 0, rec.payslip_custom_id.payslip_custom_line_ids.ids)]
            else:
                rec.line_ids = [(6, 0, [])]

    @api.multi
    @api.depends('payroll_type', 'line_ids')
    def get_type_amount(self):
        for rec in self:
            rec.type_amount = 0.0
            if rec.payroll_type == 'basic_salary':
                rec.type_amount = sum(rec.line_ids.mapped('basic_salary'))
            if rec.payroll_type == 'transport_allowance':
                rec.type_amount = sum(rec.line_ids.mapped('transport_allowance'))
            if rec.payroll_type == 'utilities_allowance':
                rec.type_amount = sum(rec.line_ids.mapped('utilities_allowance'))
            if rec.payroll_type == 'house_Rent_Allowance':
                rec.type_amount = sum(rec.line_ids.mapped('house_Rent_Allowance'))
            if rec.payroll_type == 'employee_benefit_gratuity_loan':
                rec.type_amount = sum(rec.line_ids.mapped('employee_benefit_gratuity_loan'))
            if rec.payroll_type == 'overtime_odp':
                rec.type_amount = sum(rec.line_ids.mapped('overtime_odp'))
            if rec.payroll_type == 'monthly_gross_pay':
                rec.type_amount = sum(rec.line_ids.mapped('monthly_gross_pay'))
            if rec.payroll_type == 'total_monthly_gross_pay':
                rec.type_amount = sum(rec.line_ids.mapped('total_monthly_gross_pay'))
            if rec.payroll_type == 'paye':
                rec.type_amount = sum(rec.line_ids.mapped('paye'))
            if rec.payroll_type == 'advance_salary':
                rec.type_amount = sum(rec.line_ids.mapped('advance_salary'))
            if rec.payroll_type == 'nhf':
                rec.type_amount = sum(rec.line_ids.mapped('nhf'))
            if rec.payroll_type == 'pension':
                rec.type_amount = sum(rec.line_ids.mapped('pension'))
            if rec.payroll_type == 'loan_repayment':
                rec.type_amount = sum(rec.line_ids.mapped('loan_repayment'))
            if rec.payroll_type == 'absent_odp_penalty':
                rec.type_amount = sum(rec.line_ids.mapped('absent_odp_penalty'))
            if rec.payroll_type == 'total_deductions':
                rec.type_amount = sum(rec.line_ids.mapped('total_deductions'))
            if rec.payroll_type == 'net_pay':
                rec.type_amount = sum(rec.line_ids.mapped('net_pay'))



class HRPayslipCustomLine(models.Model):
    _name = 'hr.payslip.custom.line'

    payslip_custom_id = fields.Many2one('hr.payslip.custom',string="Payslip Custom Id")
    staff_id = fields.Char(string="Staff Id")
    payment_mode = fields.Char("Account details")
    designation_place = fields.Char(string="Place of Designation")
    employe_name = fields.Many2one('hr.employee',string="Names of Employees")
    function = fields.Many2one('hr.department', string="Function")
    position = fields.Many2one('hr.job', string="Position")
    basic_salary = fields.Float("Basic Salary")
    transport_allowance = fields.Float("Transport Allowance")
    utilities_allowance = fields.Float("Utilities Allowance")
    house_Rent_Allowance = fields.Float("House Rent Allowance")
    employee_benefit_gratuity_loan = fields.Float("Employee Benefit/Gratuity")
    overtime_odp = fields.Float("OVERTIME/ODP")
    monthly_gross_pay = fields.Float("Monthly Gross Pay")
    total_monthly_gross_pay = fields.Float("Total Monthly Gross Pay")
    paye = fields.Float("PAYE")
    advance_salary = fields.Float("ADVANCE SALARY")
    nhf = fields.Float("NHF")
    pension = fields.Float("PENSION")
    loan_repayment = fields.Float("LOAN REPAYMENT")
    absent_odp_penalty = fields.Float("ABSENT/ODP/PENALTY")
    total_deductions = fields.Float("TOTAL DEDUCTIONS")
    net_pay = fields.Float("NET PAY")
    hourly_pay = fields.Float("Hourly Pay")
    hourly_worked = fields.Float("Hourly Worked")
    overtime = fields.Float("Overtime")
    amount = fields.Float("Overtime Amount")
    days_worked = fields.Float('Days Worked')
    daily_pay = fields.Float('Daily Pay')
    off_duty_working = fields.Float('Off Duty Working')

    @api.multi
    @api.onchange('amount','off_duty_working')
    def on_change_overtime_odp(self):
        self.overtime_odp = self.amount + self.off_duty_working

    @api.multi
    @api.onchange('paye', 'advance_salary', 'nhf', 'pension', 'loan_repayment', 'absent_odp_penalty')
    def onchange_total_deduction(self):
        self.total_deductions = self.paye + self.advance_salary + self.nhf + self.pension + self.loan_repayment + self.absent_odp_penalty


    @api.multi
    @api.onchange('days_worked', 'daily_pay')
    def onchange_daily_overtime(self):
        self.off_duty_working = self.days_worked * self.daily_pay

    @api.multi
    @api.onchange('hourly_pay', 'hourly_worked', 'overtime')
    def onchange_hourly_overtime(self):
        self.amount = self.overtime * self.hourly_worked

    @api.multi
    @api.onchange('total_monthly_gross_pay', 'total_deductions')
    def onchange_net_pay(self):
        self.net_pay = self.total_monthly_gross_pay - self.total_deductions

    @api.multi
    @api.onchange('basic_salary', 'transport_allowance', 'utilities_allowance', 'house_Rent_Allowance',
                  'off_duty_working', 'overtime', 'employee_benefit_gratuity_loan', 'overtime_odp')
    def onchange_amount(self):
        self.monthly_gross_pay = self.basic_salary + self.transport_allowance + self.utilities_allowance +self.house_Rent_Allowance
        self.total_monthly_gross_pay = self.basic_salary + self.transport_allowance + self.utilities_allowance + self.house_Rent_Allowance + self.employee_benefit_gratuity_loan + self.overtime_odp

    @api.multi
    @api.onchange('monthly_gross_pay')
    def onchange_monthly_gross_pay(self):
        if self.monthly_gross_pay:
            self.basic_salary = self.monthly_gross_pay * 45 / 100
            self.transport_allowance = self.monthly_gross_pay * 25 / 100
            self.utilities_allowance = self.monthly_gross_pay * 10 / 100
            self.house_Rent_Allowance = self.monthly_gross_pay * 20 / 100
            # pension = self.basic_salary + self.transport_allowance + self.house_Rent_Allowance
            # self.pension = (pension * 8) / 100 if pension else 0.0

    @api.multi
    @api.onchange('employe_name')
    def onchange_employee_name(self):
        if self.employe_name:
            self.function = self.employe_name.department_id and self.employe_name.department_id.id or False
            self.position = self.employe_name.job_id.id
            self.designation_place = self.employe_name.work_location
            self.monthly_gross_pay = self.employe_name.gross_monthly_pay or 0.0
            self.staff_id = self.employe_name.employee_unique_code
            self.payment_mode = self.employe_name.account_details

    # @api.multi
    # def generate_payslip(self):
    #     return self.env.ref('fastra_hr_customize.report_hr_payroll_line_sheet').report_action(self)