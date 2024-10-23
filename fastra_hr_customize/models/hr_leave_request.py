from odoo import fields, models, api


class HrLeaveRequest(models.Model):
    _name = 'fastra.leave.request'
    _inherit = ['mail.thread']

    state = fields.Selection([
        ('draft', 'Draft'),
        ('send_hod', 'Send To HOD'),
        ('send_hr', 'Send To HR'),
        ('send_md', 'Send To MD'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ], string='Status', index=True, readonly=True, default='draft', )

    hr_employee_id = fields.Many2one('hr.employee', string="Name")
    designation = fields.Char("Designation")
    date_of_joining = fields.Date("Date joining")
    contact_no = fields.Integer("Contact No")
    department = fields.Char("Department")
    leave_line_ids = fields.One2many('fastra.leave.lines', 'leave_request_id', string="Leave Lines")
    leave_history_line_ids = fields.One2many('fastra.leave.history.lines', 'leave_request_id', string="Leave History Lines")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    location_id = fields.Many2one('stock.location', string="Location")

    @api.onchange('hr_employee_id')
    def onchange_hr_employee_id(self):
        if self.hr_employee_id:
            self.designation = self.hr_employee_id.work_location

    def send_hod(self):
        self.state = 'send_hod'

    def send_hr(self):
        self.state = 'send_hr'

    def send_md(self):
        self.state = 'send_md'

    def approve(self):
        self.state = 'approve'

    def set_draft(self):
        self.state = 'draft'

    def reject(self):
        self.state = 'reject'


class FastraLeaveLines(models.Model):
    _name = 'fastra.leave.lines'

    leave_type_id = fields.Many2one('fastra.leave.type', string="Type of Leave")
    leave_from = fields.Date("Leave from")
    leave_to = fields.Date("Leave to")
    duration_of_leave = fields.Float("Duration of Leaves Approved")
    document_to_cover = fields.Selection([('yes', 'Yes'),
                                          ('no', 'No')], string="Document to cover")
    leave_request_id = fields.Many2one('fastra.leave.request', string="Leave Request Id")
    leave_balance = fields.Integer("Leave Balance", compute="get_leave_balance")
    leave_allocated = fields.Integer("Leave Allocated")
    comment = fields.Text("Comment")

    @api.multi
    @api.depends('leave_allocated', 'duration_of_leave')
    def get_leave_balance(self):
        for rec in self:
            rec.leave_balance = rec.leave_allocated - rec.duration_of_leave


class LeavesHistoryLines(models.Model):
    _name = 'fastra.leave.history.lines'

    leave_type_id = fields.Many2one('fastra.leave.type', string="Type of Leave")
    leave_from = fields.Date("Leave from")
    leave_to = fields.Date("Leave to")
    duration_of_leave = fields.Float("Duration of Leaves")
    document_to_cover = fields.Selection([('yes', 'Yes'),
                                          ('no', 'No')], string="Document to cover")
    leave_request_id = fields.Many2one('fastra.leave.request', string="Leave Request Id")
    comment = fields.Text("Comment")


class FastraLeaveType(models.Model):
    _name = 'fastra.leave.type'

    name = fields.Char("Name")
