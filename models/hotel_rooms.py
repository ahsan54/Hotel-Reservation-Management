from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime
from odoo.exceptions import UserError


class RoomTypeSpecify(models.Model):
    _name = 'room.type'
    _rec_name = 'room_type'

    room_image = fields.Binary(string="Room Image", attachment=True)

    ac_facility = fields.Boolean('A/C', default=False)
    ac_facility_price = fields.Float('A/C Price', default=0.0)

    heater_facility = fields.Boolean('Heater', default=False)
    heater_facility_price = fields.Float('Heater Price', default=0.0)

    gym_facility = fields.Boolean('Gym', default=False)
    gym_facility_price = fields.Float('Gym Price', default=0.0)

    room_base_price = fields.Float('Base Price', digits=(16, 2))
    room_price_included_facility = fields.Float('Total Price', digits=(16, 2))

    room_type = fields.Char('Room Type', compute='_compute_room_type')

    @api.depends('ac_facility', 'heater_facility', 'gym_facility')
    def _compute_room_type(self):
        for type in self:
            if type.ac_facility and type.heater_facility and type.gym_facility:
                type.room_type = 'Luxury Suite'
            elif type.ac_facility and type.heater_facility:
                type.room_type = 'Executive Room'
            elif type.ac_facility and type.gym_facility:
                type.room_type = 'Wellness Suite'
            elif type.heater_facility and type.gym_facility:
                type.room_type = 'Spa Retreat Room'
            elif type.ac_facility:
                type.room_type = 'Deluxe Room'
            elif type.heater_facility:
                type.room_type = 'Cozy Winter Room'
            elif type.gym_facility:
                type.room_type = 'Fitness Suite'
            else:
                type.room_type = 'N/A'

    @api.onchange('room_base_price', 'ac_facility_price', 'heater_facility_price', 'gym_facility_price')
    def _onchange_total_price(self):
        for room in self:
            total_price = room.room_base_price

            # **Handle different cases explicitly**
            if room.ac_facility and room.heater_facility and room.gym_facility:
                total_price += room.ac_facility_price + room.heater_facility_price + room.gym_facility_price
            elif room.ac_facility and room.heater_facility:
                total_price += room.ac_facility_price + room.heater_facility_price
            elif room.ac_facility and room.gym_facility:
                total_price += room.ac_facility_price + room.gym_facility_price
            elif room.heater_facility and room.gym_facility:
                total_price += room.heater_facility_price + room.gym_facility_price
            elif room.ac_facility:
                total_price += room.ac_facility_price
            elif room.heater_facility:
                total_price += room.heater_facility_price
            elif room.gym_facility:
                total_price += room.gym_facility_price

            room.room_price_included_facility = total_price


class CreateRooms(models.Model):
    _name = 'hotel.room'
    _rec_name = 'room_type_id'

    room_type_id = fields.Many2one('room.type', string='Room Type')

    hotel_base_id = fields.Many2one('hotel.base')
    name = fields.Char(readonly=True, copy=False, default=lambda self: self._get_next_sequence())
    state = fields.Selection([('draft', 'Available'), ('done', 'Booked')], default='draft')
    ac_facility = fields.Boolean('A/C', related='room_type_id.ac_facility', readonly=True)
    heater_facility = fields.Boolean('Heater', related='room_type_id.heater_facility', readonly=True)
    gym_facility = fields.Boolean('Gym', related='room_type_id.gym_facility', readonly=True)
    room_price = fields.Float('Room Price', digits=(16, 2), related='room_type_id.room_price_included_facility',
                              readonly=True)
    room_image = fields.Binary(string="Room Image", attachment=True, related='room_type_id.room_image')

    guest_id = fields.Many2one('hotel.base', 'Guest', readonly=True)

    # Use a write override instead of onchange
    @api.model_create_multi
    def create(self, vals_list):
        rooms = super().create(vals_list)
        for room in rooms:
            if room.state == 'done':
                self._create_booking_log(room)
        return rooms

    def write(self, vals):
        result = super().write(vals)
        if 'state' in vals and vals['state'] == 'done':
            for room in self:
                self._create_booking_log(room)
        return result

    def _create_booking_log(self, room):
        room_booking_user_cnic = 0
        room_booking_user_name = ''
        booked_date = fields.Date()
        check_out_date = fields.Date()
        guest_id_details = self.env['hotel.base'].search([('name', '=', self.guest_id.name)])
        if guest_id_details:
            print(f'Guest ID Details: {guest_id_details}')
            room_booking_user_cnic = guest_id_details.guest_cnic
            room_booking_user_name = guest_id_details.guest_name
            booked_date = guest_id_details.date_ordered
            check_out_date = guest_id_details.check_out_date

        self.env['room.booked.logs'].create({
            'room_booked': True,
            'room_booked_date': booked_date,
            'room_check_out_date': check_out_date,
            'room_id': room.id,  # Reference to the room
            'room_image': room.room_image,
            'room_price': room.room_price,
            'room_seq': room.name,
            'room_booking_user_cnic': room_booking_user_cnic,
            'room_booking_user_name': room_booking_user_name,
        })

    def button_reset(self):
        for x in self:
            obj = self.env['hotel.base'].search([('name', '=', x.guest_id.name)])
            print('-:-', obj)
            obj.button_cancel()
            x.update({'state': 'draft'})

    @api.model
    def _get_next_sequence(self):
        """Fetches the next sequence without incrementing it."""
        seq_obj = self.env['ir.sequence'].sudo()
        seq_id = seq_obj.search([('code', '=', 'hotel.room.creation.sequence')], limit=1)
        x = f'ROOM#{seq_id.number_next_actual:010d}'
        return x if seq_id else _('New')

    @api.model
    def create(self, vals):
        """Assigns the sequence and ensures it is only incremented on record creation."""
        if not vals.get('name') or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hotel.room.creation.sequence')
        return super(CreateRooms, self).create(vals)

    def unlink(self):
        """Rollback sequence if the record is not saved."""
        seq_obj = self.env['ir.sequence'].sudo()
        seq_id = seq_obj.search([('code', '=', 'hotel.room.creation.sequence')], limit=1)
        if seq_id and self.name and self.name.isdigit():
            seq_id.write({'number_next_actual': int(self.name)})  # Reverting sequence
        return super(CreateRooms, self).unlink()


class RoomBookedHistory(models.Model):
    _name = 'room.booked.logs'
    _description = 'Room Booking History'
    _order = 'room_booked_date desc'

    room_id = fields.Many2one('hotel.room', string='Room')
    room_booked_date = fields.Date('Room Booked Date')
    room_check_out_date = fields.Date('Room Check Out Date')
    room_seq = fields.Char('Sequence')
    room_booked = fields.Boolean('Room Booked')
    room_image = fields.Binary(string="Room Image", attachment=True)
    room_price = fields.Float('Room Price', digits=(16, 2), readonly=True)
    room_booking_user_cnic = fields.Char('User CNIC')
    room_booking_user_name = fields.Char('User Name')
