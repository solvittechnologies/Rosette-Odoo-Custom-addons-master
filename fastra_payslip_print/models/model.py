# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class ReportHRPayslipCustomLibeReportWizard(models.TransientModel):
    _name = 'report.fastra_payslip_print.report.wizard'

    payment_mode = fields.Boolean("Mode Of Payment")
    designation_place = fields.Boolean(string="Place of Designation")
    employe_name = fields.Boolean(string="Names of Employees")
    function = fields.Boolean(string="Function")
    position = fields.Boolean("Position")
    basic_salary = fields.Boolean("Basic Salary")
    transport_allowance = fields.Boolean("Transport Allowance")
    utilities_allowance = fields.Boolean("Utilities Allowance")
    house_Rent_Allowance = fields.Boolean("House Rent Allowance")
    employee_benefit_gratuity_loan = fields.Boolean("Employee Benefit/Gratuity/Loan")
    overtime_odp = fields.Boolean("OVERTIME/ODP")
    monthly_gross_pay = fields.Boolean("Monthly Gross Pay")
    total_monthly_gross_pay = fields.Boolean("Total Monthly Gross Pay")
    paye = fields.Boolean("PAYE")
    advance_salary = fields.Boolean("ADVANCE SALARY")
    nhf = fields.Boolean("NHF")
    pension = fields.Boolean("PENSION")
    loan_repayment = fields.Boolean("LOAN REPAYMENT")
    absent_odp_penalty = fields.Boolean("ABSENT/ODP/PENALTY")
    total_deductions = fields.Boolean("TOTAL DEDUCTIONS")
    net_pay = fields.Boolean("NET PAY")
    hourly_pay = fields.Boolean("Hourly Pay")
    hourly_worked = fields.Boolean("Hourly Worked")
    overtime = fields.Boolean("Overtime")
    amount = fields.Boolean("Overtime Amount")
    days_worked = fields.Boolean('Days Worked')
    daily_pay = fields.Boolean('Daily Pay')
    off_duty_working = fields.Boolean('Off Duty Working')

    resid = fields.Integer("res id")

    @api.multi
    def get_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'values':self.id
        }
        return self.env.ref('fastra_payslip_print.hr_payslip_custom_report').report_action(self,data)

class ReportHRPayslipCustomLibeReportView(models.AbstractModel):
    _name = 'report.fastra_payslip_print.hr_payslip_custom_report_view'
    
    @api.model
    def _get_report_values(self, docids, data):

        getwizardValue=self.env['report.fastra_payslip_print.report.wizard'].sudo().search([('id','=',data['values'])])


        doc= self.env['hr.payslip.custom.line'].sudo().search([('id','=',getwizardValue.resid)])
        # currency=self.env.ref("base.main_company").currency_id
        company= doc.payslip_custom_id.company_id
        currency = company.currency_id
        
        return {
            'doc_ids': data['ids'],
            'doc_model': "hr.payslip.custom.line",
            'docs':doc,
            'currency':currency,
            'company':company,
            'o':doc,
            'getwizardValue':getwizardValue
        }

class HRPayslipCustomLibeReport(models.Model):
    _inherit = "hr.payslip.custom.line"

    def launch_wizard(self):
        wizard_id = self.env['report.fastra_payslip_print.report.wizard'].create({"resid": self.id}).id
        return {
            'name': 'My Wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'report.fastra_payslip_print.report.wizard',
            'res_id': wizard_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
 

    
    

# class HRPayslipCustomLibeReport(models.Model):
#     _inherit = "hr.payslip.custom"
    
 

#     @api.multi
#     def get_all_report(self):
#         _logger.error(self.payslip_custom_line_ids)
#         for d in self.payslip_custom_line_ids:
#             _logger.error("_logger.error(d)_logger.error(d)_logger.error(d)")
#             _logger.error(d)
#             return self.env.ref('fastra_payslip_print.hr_payslip_custom_report').report_action(d.id)