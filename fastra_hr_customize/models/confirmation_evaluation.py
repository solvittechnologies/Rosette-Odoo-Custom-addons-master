from odoo import fields, models, api,_


class ConfirmationEvaluation(models.Model):
    _name = 'hr.confirmation.evaluation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'HR Confirmation Evaluation'
    _rec_name = 'employee'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('send_for_approval', 'Send For Approval'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        # ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
    )
    rejection_note = fields.Text("Rejection Note")
    employee = fields.Many2one('hr.employee', string="EMPLOYEE NAME")
    superior_name = fields.Char("SUPERIOR'S NAME")
    date_of_joining = fields.Date('DATE OF JOINING')
    salary = fields.Float('SALARY')
    company_name = fields.Char('COMPANY NAME/LOCATION')
    present_position = fields.Char('PRESENT POSITION/DESIGNATION')
    employee_current_scop_work = fields.Char("EMPLOYEE'S CURRENT SCOPE OF WORK")
    superior_line_ids = fields.One2many('hr.confirmation.evaluation.superior.line', 'confirmation_evaluation_id', string="Superior Line")
    hr_line_ids = fields.One2many('hr.confirmation.evaluation.hr.line', 'confirmation_evaluation_id', string="HR Line")

    recommended_confirmation_terminated = fields.Char(
        "Why should the employee be recommended for confirmation or services be terminated?")
    technical_training_manager = fields.Char("Technical/Professional Training needs identified by the Manager")
    behavioral_training_required = fields.Char("Behavioral Training Required")
    confirmation_done_by_id = fields.Char(string="Confirmation commendation done by")
    job_position_id = fields.Char(string="Designation")
    date = fields.Date("Signature and Date")

    any_misconduct_noticed_by_the_location_hr_department = fields.Char(
        "ANY MISCONDUCT NOTICED BY THE LOCATION HR DEPARTMENT")
    hod_id = fields.Char(string="COMMENTS VERIFIED BY HOD")
    designation = fields.Char("Designation")
    date = fields.Date("SIGNATURE & DATE")
    approved_by_id = fields.Char(string="APPROVED BY")
    supervisor_id = fields.Char(string="Supervisor")
    hr_executive_id = fields.Char(string="HR Executive")
    executive_director_id = fields.Char(string="Executive Director")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id.id)

    @api.multi
    @api.onchange('confirmation_done_by_id')
    def onchange_confirmation_done_by_id(self):
        if self.confirmation_done_by_id:
            self.job_position_id = self.confirmation_done_by_id.job_id and self.confirmation_done_by_id.job_id.id or False

    def send_approval(self):
        self.state = 'send_for_approval'

    def approve(self):
        self.state = 'approve'

    def reject(self):
        action = {
            'name': _('Rejection Confirmation'),
            'view_mode': 'form',
            'res_model': 'confirmation.evaluation.reject',
            'view_id': self.env.ref('fastra_hr_customize.view_confirmation_evaluation_reject_form').id,
            'type': 'ir.actions.act_window',
            'context': {'default_hr_confirmation_evaluation_id': self.id},
            'target': 'new'
        }
        return action

class ConfirmationEvaluationSuperiorLine(models.Model):
    _name = 'hr.confirmation.evaluation.superior.line'

    confirmation_evaluation_id = fields.Many2one('hr.confirmation.evaluation', string="Confirmation Evaluation")
    assessment_criteria_id = fields.Many2one('assessment.criteria', string="ASSESSMENT CRITERIA")
    excellent = fields.Char("5 (EXCELLENT)")
    very_good = fields.Char("4 (VERY GOOD)")
    good = fields.Char("3 (GOOD)")
    poor = fields.Char("2 (POOR)")
    very_poor = fields.Char("1 (VERY POOR)")
    is_excellent = fields.Boolean()
    is_very_good = fields.Boolean()
    is_good = fields.Boolean()
    is_poor = fields.Boolean()
    is_very_poor = fields.Boolean()

    @api.multi
    @api.onchange('assessment_criteria_id')
    def onchange_assessment_criteria_id(self):
        if self.assessment_criteria_id:
            self.excellent = self.assessment_criteria_id.excellent
            self.very_good = self.assessment_criteria_id.very_good
            self.good = self.assessment_criteria_id.good
            self.poor = self.assessment_criteria_id.poor
            self.very_poor = self.assessment_criteria_id.very_poor

    @api.multi
    @api.onchange('is_excellent')
    def onchange_line_is_excellent(self):
        if self.is_excellent == True:
            self.is_very_good = False
            self.is_good = False
            self.is_poor = False
            self.is_very_poor = False

    @api.multi
    @api.onchange('is_very_good')
    def onchange_line_is_very_good(self):
        if self.is_very_good == True:
            self.is_excellent = False
            self.is_good = False
            self.is_poor = False
            self.is_very_poor = False

    @api.multi
    @api.onchange('is_good')
    def onchange_line_is_good(self):
        if self.is_good == True:
            self.is_excellent = False
            self.is_very_good = False
            self.is_poor = False
            self.is_very_poor = False

    @api.multi
    @api.onchange('is_poor')
    def onchange_line_is_poor(self):
        if self.is_poor == True:
            self.is_excellent = False
            self.is_very_good = False
            self.is_good = False
            self.is_very_poor = False

    @api.multi
    @api.onchange('is_very_poor')
    def onchange_line_is_very_poor(self):
        if self.is_very_poor == True:
            self.is_excellent = False
            self.is_very_good = False
            self.is_good = False
            self.is_poor = False

class ConfirmationEvaluationHrLine(models.Model):
    _name = 'hr.confirmation.evaluation.hr.line'

    confirmation_evaluation_id = fields.Many2one('hr.confirmation.evaluation', string="Confirmation Evaluation")
    leave_authorized_by_company_policy = fields.Integer("LEAVE AUTHORIZED BY THE COMPANY POLICY (No of Days)")
    other_leave_taken_on_request = fields.Integer("OTHER LEAVE TAKEN ON REQUEST (No of Days)")
    leave_taken_without_request = fields.Integer("LEAVE TAKEN WITHOUT REQUEST (No of Days)")
    no_of_query_received_during_period = fields.Integer('NO OF QUERIES RECEIVED DURING THE PERIOD')
    no_of_warning_received_during_period = fields.Integer('NO OF WARNINGS RECEIVED DURING THE PERIOD')
    no_of_suspensions_received_during_period = fields.Integer('NO OF SUSPENSIONS RECEIVED DURING THE PERIOD')
    any_letters_of_commendation_from_superior = fields.Integer('ANY LETTER(S) OF COMMENDATION FROM SUPERIOR(S)')
