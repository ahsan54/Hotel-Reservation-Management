from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta
from odoo.exceptions import UserError

class CheckInRequest(models.Model):
    _name = 'hotel.base'
    _description = 'Hotel Management'

    name = fields.Char(readonly=True, copy=False, default=lambda self: _('New'))
    state = fields.Selection([('draft', 'Draft'), ('cancel', 'Cancel'), ('done', 'Done')], default='draft')
    guest_name = fields.Char(string='Guest Name')
    guest_cnic = fields.Integer(string='CNIC', sql_type='bigint')
    date_ordered = fields.Date('Date Ordered')
    check_out_date = fields.Date('Check Out Date')
    stay_days = fields.Integer('Stay Days', compute='_compute_stay_days')
    notes = fields.Text('Notes')
    price = fields.Char(string='Room Price')
    room_number = fields.Many2one('hotel.room', string='Room', readonly=True)
    hotel_room_ids = fields.One2many('hotel.room', 'hotel_base_id', 'Hotel Room IDs')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hotel.base.sequence') or _('New')
            print(f"Generated Reference No: {vals['name']}")
        return super(CheckInRequest, self).create(vals)

    def button_cancel(self):
        for record in self:
            print('called')
            record.sudo().unlink()

    def button_done(self):
        for x in self:
            user_room_book_id = self.env['hotel.room'].search([('name', '=', self.room_number.name)])
            print('User Id: ', user_room_book_id.id, user_room_book_id.name)
            if user_room_book_id:
                user_room_book_id.write({'state': 'done', 'guest_id': x.id})
            x.update({'state': 'done'})

        room_image = fields.Binary()
        room_image_id = self.env['hotel.room'].search([('name', '=', self.room_number.name)])
        print(room_image_id)
        if room_image_id:
            room_image = room_image_id.room_image
        for past in self:
            guest_history = self.env['guest.history'].create({
                'guest_cnic': past.guest_cnic,
                'date_ordered': past.date_ordered,
                'guest_name': past.guest_name,
                'room_number': past.room_number.room_type_id.room_type,
                'notes': past.notes,
                'price': past.price,
                'check_out_date': past.check_out_date,
                'stay_days': past.stay_days,
                'room_image': room_image,
            })

    @api.depends('date_ordered', 'check_out_date')
    def _compute_stay_days(self):
        for record in self:
            if record.date_ordered and record.check_out_date:
                record.stay_days = (record.check_out_date - record.date_ordered).days + 1
            else:
                record.stay_days = 0


class CheckOutRequest(models.Model):
    _name = 'approval.check.out'
    _description = 'Approval Check Out Request'

    display_name = fields.Char(string='Display Name')
    guest_id = fields.Many2one('hotel.base', string='Guest', readonly=True)
    guest_seq = fields.Char(string='Guest Seq', related='guest_id.name')
    guest_name = fields.Char(string='Guest Name', related='guest_id.guest_name')
    guest_room = fields.Char(string='Guest Room', related='guest_id.room_number.room_type_id.room_type')


class GuestHistory(models.Model):
    _name = 'guest.history'
    _description = 'Guest History'

    guest_cnic = fields.Integer(string='CNIC')
    guest_name = fields.Char(string='Guest Name')
    date_ordered = fields.Date('Date Ordered')
    check_out_date = fields.Date('Check Out Date')
    stay_days = fields.Integer('Stay Days')
    notes = fields.Text('Notes')
    price = fields.Char(string='Room Price')
    room_number = fields.Char(string='Room Number')
    room_image = fields.Binary(string='Room Image')