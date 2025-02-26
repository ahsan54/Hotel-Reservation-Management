from odoo import http, fields, _
from odoo.addons.base.models.ir_actions_report import available
from odoo.exceptions import ValidationError
from odoo.http import request
from datetime import date, datetime
from datetime import date, timedelta
import calendar

from odoo import http, fields
from datetime import date, timedelta
import logging

_logger = logging.getLogger(__name__)

from odoo import http, fields
from datetime import date, timedelta
import logging

_logger = logging.getLogger(__name__)


class DashBoard_Filter_Check_Ins(http.Controller):
    @http.route(['/dashboard', '/filter/check_ins'], type='http', auth='public', website=True, methods=['GET'])
    def filter_check_ins(self, **kwargs):
        print(f':--- { 2         }')
        bookings_list = []
        check_out_list = []
        selected_month = None
        request_type = kwargs.get('request_type', 'check_in')  # Default to check-in if not specified

        # Only process if a valid month is provided
        if kwargs.get('require_month') and kwargs.get('require_month') != 'Select Month':
            require_date = fields.Date.from_string(kwargs.get('require_month'))
            selected_month = require_date.strftime("%B %Y")
            month_start = date(require_date.year, require_date.month, 1)
            if require_date.month == 12:
                month_end = date(require_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(require_date.year, require_date.month + 1, 1) - timedelta(days=1)

            # Check-in Requests (room.booked.logs)
            if request_type == 'check_in':
                booking_records = request.env['room.booked.logs'].sudo().search([
                    ('room_booked_date', '>=', month_start),
                    ('room_booked_date', '<=', month_end),
                    ('room_booked', '=', True)
                ])

                if booking_records:
                    for x in booking_records:
                        room_image = x.room_image
                        if room_image and isinstance(room_image, bytes):
                            room_image = room_image.decode('utf-8')  # Keep as per your request
                        elif not room_image:
                            room_image = None

                        bookings_list.append({
                            'room_booked_date': x.room_booked_date.strftime('%Y-%m-%d'),
                            'room_check_out_date': x.room_check_out_date.strftime('%Y-%m-%d'),
                            'room_image': room_image,
                            'room_price': x.room_price,
                            'room_name': x.room_id.room_type_id.room_type if x.room_id.room_type_id else 'N/A',
                            'room_seq_no': x.room_id.name if x.room_id else 'N/A',
                        })

            # Check-out Requests (guest.history)
            elif request_type == 'check_out':
                check_out_records = request.env['guest.history'].sudo().search([
                    ('check_out_date', '>=', month_start),
                    ('check_out_date', '<=', month_end)
                ])

                if check_out_records:
                    for x in check_out_records:
                        room_image = x.room_image  # Now available in guest.history
                        if room_image and isinstance(room_image, bytes):
                            room_image = room_image.decode('utf-8')  # Keep as per your request
                        elif not room_image:
                            room_image = None

                        check_out_list.append({
                            'id': x.id,
                            'guest_name': x.guest_name or 'N/A',
                            'room_number': x.room_number or 'N/A',
                            'date_ordered': x.date_ordered.strftime('%Y-%m-%d') if x.date_ordered else 'N/A',
                            'check_out_date': x.check_out_date.strftime('%Y-%m-%d') if x.check_out_date else 'N/A',
                            'price': x.price or '0.0',
                            'stay_days': x.stay_days or 0,
                            'room_image': room_image,  # Use the new room_image field from guest.history
                        })

        # Additional Data for All Guests and Rooms
        all_guests = []
        all_rooms = []
        all_guests_ids = request.env['hotel.base'].sudo().search([('state', '=', 'done')])
        all_room_ids = request.env['hotel.room'].sudo().search([])

        for guest in all_guests_ids:
            all_guests.append({
                'guest_name': guest.guest_name or 'N/A',
                'guest_cnic': guest.guest_cnic or 'N/A',
                'date_ordered': guest.date_ordered.strftime('%Y-%m-%d') if guest.date_ordered else 'N/A',
                'check_out_date': guest.check_out_date.strftime('%Y-%m-%d') if guest.check_out_date else 'N/A',
                'stay_days': guest.stay_days or 0,
                'price': guest.price or '0.0',
            })

        for room in all_room_ids:
            room_image = room.room_image
            if room_image and isinstance(room_image, bytes):
                room_image = room_image.decode('utf-8')  # Keep as per your request
            elif not room_image:
                room_image = None

            all_rooms.append({
                'status': room.state,
                'ac_facility': room.ac_facility,
                'heater_facility': room.heater_facility,
                'gym_facility': room.gym_facility,
                'room_price': room.room_price,
                'room_image': room_image,
                'guest_id': room.guest_id.name if room.guest_id else 'N/A',
            })

        return request.render('hotel_management.dashboard_controller_sub_view_id_1', {
            'bookings_list': bookings_list,
            'check_out_list': check_out_list,
            'selected_month': selected_month,
            'request_type': request_type,
            'all_guests': all_guests,
            'all_rooms': all_rooms,
        })
