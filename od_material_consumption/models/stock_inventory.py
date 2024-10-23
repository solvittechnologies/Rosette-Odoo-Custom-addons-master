from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    picking_type_id = fields.Many2one('stock.picking.type',string='Operation Type')

    # Override default location and change code
    @api.model
    def _default_location_id(self):
        location = self.env['stock.location'].search([('store_keeper', '=', self.env.uid)])
        if len(location) > 0:
            return location[0].id
        else:
            raise UserError(_('You must define a location for the logged in user.'))

    @api.model
    def _get_default_approver(self):
        result = self.env['stock.location'].search([('store_keeper', '=', self.env.uid)])
        if len(result)>0:
            try:
                return result.branch_manager.id
                #return self.env['res.users'].browse(result.branch_manager.id).id
            except Exception as e:
                pass
        if len(result)<=0:
            result_store_keeper = self.env['stock.location'].search([('store_keeper', '=', self.env.uid)])
            if result_store_keeper:
                return self.env['res.users'].browse(result_store_keeper.branch_manager.id)


    @api.model
    def _get_default_location(self):
        result = self.env['stock.location'].search([('store_keeper', '=', self.env.uid)])
        if len(result)==1:
            return result.id
        if len(result)>1:
            return result[0].id


    is_material_consumption = fields.Boolean('Material Consumption')
    material_consumption_name = fields.Char('Reference', default=_('New'))
    analytical_account = fields.Many2one('account.analytic.account')
    filter = fields.Selection(default='partial')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancle', 'Reject'),
        ('confirm', 'Approval'),
        ('done', 'Released')
    ], default='draft')

    store_keeper = fields.Many2one("res.users", String='Store Keeper', default=lambda self: self.env.user)
    project_manager = fields.Many2one("res.users", String='Project Manager', default=_get_default_approver)
    partner = fields.Char()
    source_location = fields.Many2one('stock.location')
    operation_type = fields.Many2one('stock.picking.type')
    site_name = fields.Many2one('stock.location', default=_default_location_id)
    current_user = fields.Many2one("res.users")
    # date_release = fields.Date("Request Date", default=datetime.date(datetime.now()))
    date = fields.Date("Request Date", default=datetime.date(datetime.now()))
    # request_date = fields.Date("Request Date")
    shipping_policy = fields.Selection([
        ('draft', 'Receive each product when available '),
        ('request', 'Receive all product at once'),
    ], default='draft')
    # procurement_group = fields.Char(readony=1)
    # priority = fields.Selection([
    #     ('not_urgent', 'Not urgent'),
    #     ('normal', 'Normal'),
    #     ('urgent', 'Urgent'),
    #     ('very_urgent', 'Very Urgent'),
    # ])
    product_category = fields.Many2one('product.category')
    journal_id = fields.Many2one('account.move', readonly=1)
    project_id = fields.Many2one('project.project', string='Project')
    location_id = fields.Many2one(
        'stock.location', 'Inventoried Location',
        readonly=True, required=True,
        states={'draft': [('readonly', False)]},
        default=_default_location_id)
    line_ids = fields.One2many(
        'stock.inventory.line', 'inventory_id', string='Inventories',
        copy=True, readonly=False,
        states={'done': [('readonly', False)]})
    is_return = fields.Boolean('Is return?', default=False)

    @api.multi
    @api.onchange('location_id')
    def onchange_location_id(self):
        self.store_keeper = self.location_id.store_keeper and self.location_id.store_keeper.id or False
        self.project_manager = self.location_id.branch_manager and self.location_id.branch_manager.id or False

    # def action_validate(self):
    #     self.generate_bill()
    #     self.reduce_quantity()
    #     return super(StockInventory, self).action_validate()

    def action_validate(self):
        if not self.site_name:
            raise UserError(_('You have to add Requesting Site for approve this.'))
        res = super(StockInventory, self).action_validate()
        for rec in self.line_ids:
            self.env['stock.quant'].create({
                'location_id': self.site_name.id,
                'product_id': rec.product_id.id,
                'quantity': -abs(rec.qty_to_consume)
            })
        return res

    def action_return(self):
        if not self.is_return:
            for rec in self:
                rec.write({'is_return': True})
                for move in rec.line_ids.filtered(lambda l: l.qty_to_return):
                    stock_quant_id = self.env['stock.quant'].search([('location_id', '=', move.location_id.id), ('product_id', '=', move.product_id.id)], limit=1)
                    if stock_quant_id:
                        stock_quant_id.write({'quantity': stock_quant_id.quantity + move.qty_to_return})

            display_record_id = self.env['display.message'].create({'name': 'Return process is successfully done.'})
            return {
                'name': _('Return Process'),
                'view_mode': 'form',
                'view_type': 'form',
                'view_id': self.env.ref('od_material_consumption.view_display_message_form').id,
                'res_model': 'display.message',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': display_record_id.id,
            }
        else:
            display_record_id = self.env['display.message'].create({'name': "Return process is already done. You can't do now!!"})
            return {
                'name': _('Return Process'),
                'view_mode': 'form',
                'view_type': 'form',
                'view_id': self.env.ref('od_material_consumption.view_display_message_form').id,
                'res_model': 'display.message',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': display_record_id.id,
            }

    @api.multi
    def generate_bill(self):
        for rec in self:
            bill_post_list = []
            bill = self.env['account.move']
            bill_line = self.env['account.move.line']
            move_lines = []
            # move_lines2 = []
            for move in rec.line_ids:
                vals = {

                    'ref': rec.material_consumption_name,
                    'consumption': True,
                    'date': rec.date,
                    'journal_id': move.product_id.categ_id.property_stock_journal.id,
                    'project_id': rec.project_id.id,
                    'picking_id': rec.id

                }

                bill_id = bill.create(vals)
                bill_post_list.append(bill_id)
                move_lines.append({
                    'move_id': bill_id.id,
                    'name': move.product_id.name,
                    'element': move.element_id.id,
                    'account_id': move.product_id.categ_id.property_account_expense_categ_id.id,
                    'analytic_account_id': move.analytical_account.id,
                    'analytic_tag_ids': (4, move.analytical_tag),
                    'debit': abs(move.product_id.standard_price * move.qty_to_consume),

                })
                move_lines.append({
                    'move_id': bill_id.id,
                    'name': move.product_id.name,
                    'element': move.element_id.id,
                    'account_id': move.product_id.categ_id.property_account_income_categ_id.id,
                    'analytic_account_id': move.analytical_account.id,
                    'analytic_tag_ids': (4, move.analytical_tag),
                    'credit': abs(move.product_id.standard_price * move.qty_to_consume),
                })

            bill_line.create(move_lines)
            for bill in bill_post_list:
                bill.sudo().action_post()
            # bill_line.create(move_lines2)

    @api.depends('current_user')
    def _get_current_user(self):
        for rec in self:
            rec.current_user = self.env.user
        # i think this work too so you don't have to loop
        self.update({'current_user': self.env.user.id})


    def reduce_quantity(self):
        for rec in self:
            # if rec.state == 'confirm':
            # self.generate_bill()

            if rec.state == "confirm":
                # rec.line_ids
                for i in rec.line_ids:
                    product = self.env['product.product'].sudo().search([('id', '=', i.product_id.id)])
                    qty_available = product.qty_available - i.qty_to_consume
                    product.sudo().write({'qty_available': qty_available})

                    # else:
                    #     i.state = 'available'
                    #     self.write({'state': 'request'})

    # @api.onchange('line_ids')
    # def reduce_quantity3(self):
    #     for rec in self:
    #         for i in rec.line_ids:
    #             product = self.env['product.product'].search([('id', '=', i.product_id.id)])
    #             i.product_qty = product.qty_available - i.qty_to_consume
    #             i.theoretical_qty = i.theoretical_qty
    #
    #         if rec.state == "confirm":
    #             # rec.line_ids
    #             for i in rec.line_ids:
    #                 product = self.env['product.product'].search([('id', '=', i.product_id.id)])
    #                 i.product_qty = product.qty_available - i.qty_to_consume

    def action_get_account_moves(self):
        form_view = self.env.ref('account.view_move_form').id
        tree_view = self.env.ref('account.view_account_move_filter').id
        get_rec = self.move_ids.ids

        return {
            'name': _('Journal Entry'),
            'domain': [('picking_id', '=', self.id), ('consumption', '=', True)],
            'view_mode': 'tree,form',
            'view_type': 'form',
            'view_id': False,
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
        }

        self.ensure_one()
        action_data = self.env['ir.actions.act_window']._for_xml_id('account.action_move_journal_line')
        action_data['domain'] = [('id', 'in', self.stock_move_id.ids)]
        return action_data

    @api.onchange('material_consumption_name')
    def onchange_material_consumption_name(self):
        if self.is_material_consumption:
            self.name = self.material_consumption_name

    @api.model
    def create(self, vals):
        if vals.get('material_consumption_name', _('New')) == _('New'):
            vals['material_consumption_name'] = self.env['ir.sequence'].next_by_code(
                'material.consumption.request') or _('New')
        res = super(StockInventory, self).create(vals)
        if res.is_material_consumption:
            res.name = res.material_consumption_name
        return res

    def action_open_inventory_lines(self):
        self.ensure_one()
        if self.is_material_consumption:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(self.env.ref('od_material_consumption.stock_consumption_line_tree').id, 'tree')],
                'view_mode': 'tree',
                'name': _('Inventory Lines'),
                'res_model': 'stock.inventory.line',
            }
            context = {
                'default_is_editable': True,
                'default_inventory_id': self.id,
                'default_company_id': self.company_id.id,
            }
            # Define domains and context
            domain = [
                ('inventory_id', '=', self.id),
                ('location_id.usage', 'in', ['internal', 'transit'])
            ]
            if self.location_ids:
                context['default_location_id'] = self.location_ids[0].id
                if len(self.location_ids) == 1:
                    if not self.location_ids[0].child_ids:
                        context['readonly_location_id'] = True

            if self.product_ids:
                if len(self.product_ids) == 1:
                    context['default_product_id'] = self.product_ids[0].id

            action['context'] = context
            action['domain'] = domain
            return action
        else:
            return super(StockInventory, self).action_open_inventory_lines()

    def action_start(self):
        for inventory in self.filtered(lambda x: x.state not in ('done','cancel')):
            vals = {'state': 'confirm'}
            if (inventory.filter != 'partial') and not inventory.line_ids:
                vals.update({'line_ids': [(0, 0, line_values) for line_values in inventory._get_inventory_lines_values()]})
            inventory.write(vals)
        return True


class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    qty_to_consume = fields.Float('Qty to Consume')
    analytical_account = fields.Many2one('account.analytic.account',string="Project")
    analytical_tag = fields.Many2one('account.analytic.tag')
    element_id = fields.Many2one('project.element', 'Element')
    description = fields.Text("Description")
    qty_to_return = fields.Float('Quantity To Return')
    date_of_line = fields.Date("Date")

    @api.model
    def create(self, vals):
        res = super(StockInventoryLine, self).create(vals)
        if vals.get('line_ids'):
            for rec in vals.get('line_ids'):
                if rec.product_id:
                    if not rec.analytical_account:
                        raise ValidationError(
                            _("Please fill Analytical Account for product %s" % (rec.product_id.name)))
                    if not rec.analytical_tag:
                        raise ValidationError(_("Please fill Analytical Tag for product %s" % (rec.product_id.name)))
        return res

    # @api.multi
    # def write(self, vals):
    #     res = super(StockInventoryLine, self).write(vals)
    #     if self.line_ids:
    #         for rec in self.ids:
    #             if rec.product_id:
    #                 if not self.analytical_account:
    #                     raise ValidationError(_("Please fill Analytical Account for product %s" %(self.product_id.name)))
    #                 if not self.analytical_tag:
    #                     raise ValidationError(_("Please fill Analytical Tag for product %s"  %(self.product_id.name)))
    #     return res

    def _get_virtual_location(self):
        if self.inventory_id.is_material_consumption:
            return self.product_id.with_context(force_company=self.company_id.id).consumption_location_id
        return super(StockInventoryLine, self)._get_virtual_location()

    # @api.onchange('qty_to_consume')
    # def _compute_product_quantity(self):
    #     for rec in self:
    #         rec.product_qty = rec.theoretical_qty - rec.qty_to_consume


class AccountMove(models.Model):
    _inherit = 'account.move'

    consumption = fields.Boolean(
        string='Consumption',
    )
    project_id = fields.Many2one('project.project', string='Project')
    picking_id = fields.Many2one('stock.inventory', string='')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    consumption = fields.Boolean(
        string='Consumption',
    )
    analytical_account = fields.Many2one('account.analytic.account')
    analytical_tag = fields.Many2one('account.analytic.tag')
    element = fields.Many2one('project.element', string="Element")


class ProjectElement(models.Model):
    _inherit = 'project.element'
