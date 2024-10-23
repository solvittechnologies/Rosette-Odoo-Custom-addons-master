# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

# class fastra__pr__p_request(models.Model):
#     _name = 'fastra__pr__p_request.fastra__pr__p_request'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100


class FastraExtention(models.Model):
    _inherit = "purchase.order"

    purchase_request_ = fields.Many2one('purchase.request', string="Purchase Request")
    location_id = fields.Many2one('stock.location', string="Location")
    description = fields.Text(string="Description")


    @api.onchange('purchase_request_')
    def porpulate_po(self):
        for rec in self:
            if rec.purchase_request_:
                for info in rec.purchase_request_:
                    # rec.date_order = str(info.date_start)
                    # rec.partner_id = info.requested_by.id
                    # rec.location = info.picking_type_id.id

                    appointment_line = [(5, 0, 0)]

                    for i in info.line_ids:
                        line = {
                            'product_id': i.product_id.id,
                            'name': i.name,
                            'date_planned': str(i.date_required),
                            'account_analytic_id': i.analytic_account_id,
                            'product_qty': i.product_qty,
                            'price_subtotal': i.estimated_cost,
                            'price_unit': i.estimated_cost / i.product_qty,
                            'analytic_tag_ids': i.analytic_tag_ids,
                            'product_uom': i.product_id.uom_id
                        }
                        appointment_line.append((0, 0, line))
                        rec.order_line = appointment_line


_STATES = [
    ('draft', 'Draft'),
    ('to_approve', 'To be approved'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('done', 'Done'),
    ('unfulfilled','unFulfilled'),
('fulfilled','Fulfilled')
]

class purchase_request_extend(models.Model):
    _inherit = "purchase.request"


    send_to = fields.Selection([(
		'procurement','Procurement'),('batching','Batching Plant')],default="procurement")
    location_id = fields.Many2one('stock.location', string="Location")
    # state2 = fields.Selection([('unfulfilled','unFulfilled'),('fulfilled','Fulfilled')],default="unfulfilled")
    # state = fields.Selection(selection=_STATES,
    #                          string='Status',
    #                          index=True,
    #                          track_visibility='onchange',
    #                          required=True,
    #                          copy=False,
    #                          default='draft')\\\\\\\\\\\\\\\\\\\\\\\\\\\


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    journal_id = fields.Many2one("account.journal")

    @api.model
    def create(self, vals):
        rec = super(AccountPayment, self).create(vals)
        if not rec.name:
            # Use the right sequence to set the name
            if rec.payment_type == 'transfer':
                sequence_code = 'account.payment.transfer'
            else:
                if rec.partner_type == 'customer':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.customer.invoice'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.customer.refund'
                if rec.partner_type == 'supplier':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.supplier.refund'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.supplier.invoice'
            rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(
                sequence_code)
            if not rec.name and rec.payment_type != 'transfer':
                raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))
        return rec
    
    @api.onchange('invoice_ids')
    def onchange_invoice_ids(self):
        total = 0.0
        for invoice in self.invoice_ids:
            total += invoice.residual_signed
        self.amount = total
            
    
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    @api.depends('amount_total')
    def _compute_amount_total_words(self):
        for sale in self:
            sale.amount_total_words=""
            if sale.currency_id:
                sale.amount_total_words = sale.currency_id.amount_to_text(sale.amount_total)

    amount_total_words = fields.Char("Total (In Words)", compute="_compute_amount_total_words")

class ResCompany(models.Model):
    _inherit = 'res.company'

    tin_number = fields.Char("Tin No")
    report_header_info = fields.Html("Report Header")
    kano_address = fields.Char("Kano Address")
    lagos_address = fields.Char("Lagos Address")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_unique_id= fields.Char(string='Customer ID',default=lambda self: _('New'))

    @api.model
    def create(self, vals):
        if vals.get('customer_unique_id', _('New')) == _('New'):
            vals['customer_unique_id'] = self.env['ir.sequence'].next_by_code(
                'res.partner.unique.customer.id.seq') or _('New')
        return super(ResPartner, self).create(vals)

