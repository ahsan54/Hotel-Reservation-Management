from odoo import http, fields, _
from odoo.addons.base.models.ir_actions_report import available
from odoo.exceptions import ValidationError
from odoo.http import request
from datetime import date, datetime


class GuestPastRoom(http.Controller):
    @http.route('/check/in/past', type='http', auth='user', methods=['GET'], website=True)
    def check_in_past_post(self, guest_cnic_input=None):
        guest_past_visits = []
        if guest_cnic_input:
            try:
                guest_cnic = int(guest_cnic_input)
            except ValueError:
                return request.redirect('/check/in')
            visits = request.env['guest.history'].sudo().search([('guest_cnic', '=', guest_cnic)])
            for visit in visits:
                guest_past_visits.append({
                    'guest_name': visit.guest_name,
                    'date_ordered': visit.date_ordered.strftime('%Y-%m-%d'),
                    'guest_cnic': visit.guest_cnic,
                    'check_out_date': visit.check_out_date.strftime('%Y-%m-%d'),
                    'stay_days': visit.stay_days,
                    'price': visit.price,
                    'room_number': visit.room_number if visit.room_number else "N/A",
                })
        return request.render('hotel_management.hotel_guest_history', {'guest_past_visits': guest_past_visits})


class CheckInRoom(http.Controller):

    @http.route('/check/in', type='http', auth='user', website=True)
    def check_in(self, **post):
        get_price = post.get('room_price')
        print(get_price)

        available_rooms = []
        room_ids = request.env['hotel.room'].search([('state', '=', 'draft')])
        for room in room_ids:
            available_rooms.append({
                'id': room.id,  # Store the room's ID
                'name': room.room_type_id.room_type,
                'price': room.room_price,
            })
            print(room.room_type_id.room_type)

        if post:
            get_guest_name = post.get('guest_name')
            get_date_ordered = post.get('date_ordered')
            get_check_out_date = post.get('check_out_date')
            get_notes = post.get('notes')
            date_ordered = fields.Date.from_string(get_date_ordered)
            check_out_date = fields.Date.from_string(get_check_out_date)
            get_price = post.get('room_price')
            guest_cnic = int(post.get('guest_cnic'))
            room_number = int(post.get('room_number'))  # Convert room ID to an integer

            today = date.today()

            # Check if date_ordered is in the past
            if date_ordered < today:
                raise ValidationError("The booking date cannot be in the past. Please select a valid date.")

            # Check if date_ordered is after check_out_date
            if date_ordered > check_out_date:
                raise ValidationError("The check-in date must be before the check-out date.")

            check_duplicate_request = request.env['hotel.base'].search(
                [('date_ordered', '=', date_ordered), ('check_out_date', '=', check_out_date),
                 ('room_number', '=', room_number)])

            if check_duplicate_request:
                raise ValidationError((f'Room {room_number} CNIC-{guest_cnic} Request Already Exists!'))

            else:
                check_in_id = request.env['hotel.base'].sudo().create({
                    'guest_name': get_guest_name,
                    'date_ordered': date_ordered,
                    'check_out_date': check_out_date,
                    'notes': get_notes,
                    'price': get_price,
                    'guest_cnic': guest_cnic,
                    'room_number': room_number,  # This now correctly stores an integer (room ID)
                })

                return request.render('hotel_management.room_booked_success_view', {})

        return request.render('hotel_management.hotel_check_in_form', {
            'available_rooms': available_rooms,
        })


class ApproveCheckIn(http.Controller):
    @http.route('/approve/check/in', type='http', auth='user', methods=['GET'], website=True)
    def get_check_in_form(self):
        # Handle only GET requests (displaying the form)
        check_ins = []
        check_in_ids = request.env['hotel.base'].sudo().search([('state', '=', 'draft')])
        for x in check_in_ids:
            check_ins.append({
                'guest_seq_name': f'{x.name} - {x.guest_name}',
            })
        return request.render('hotel_management.hotel_check_in_approval',
                              {'check_ins': check_ins}
                              )

    @http.route('/approve/check/in', type='http', auth='user', methods=['POST'], website=True)
    def post_check_in_approval(self, **post):
        # Handle only POST requests (form submission)
        if post.get('select_guest_seq_name'):
            get_seq_name = post.get('select_guest_seq_name')
            split = get_seq_name.split('-')
            split_seq = split[0].split(' ')
            seq = split_seq[0]

            check_in = request.env['hotel.base'].sudo().search([('name', '=', seq)])
            check_in.button_done()

            # Redirect to same page after successful submission
            return request.render('hotel_management.room_checked_in_success')

        return request.redirect('/approve/check/in')


# Old Code...
#
# class ApproveCheckIn(http.Controller):
#     @http.route('/approve/check/in', type='http', auth='user', website=True)
#     def approve_check_in(self, **post):
#         check_ins = []
#         check_in_ids = request.env['hotel.base'].sudo().search([('state', '=', 'draft')])
#         for x in check_in_ids:
#             check_ins.append({
#                 'guest_seq_name': f'{x.name} - {x.guest_name}',
#             })
#         print('Check INS: ',check_ins)
#
#         if post:
#             get_seq_name = post.get('select_guest_seq_name')
#             print(get_seq_name)
#             split  = get_seq_name.split('-')
#             split_seq = split[0].split(' ')
#             seq = split_seq[0]
#
#             check_in = request.env['hotel.base'].sudo().search([('name', '=', seq)])
#             print(check_in)
#             check_in.button_done()
#             print('HYYYY')
#
#         return request.render('hotel_management.hotel_check_in_approval',{'check_ins':check_ins})


class HotelPastVisitsCheck(http.Controller):
    @http.route('/past/visit', type='http', auth='user', website=True)
    def check_past(self, **kwargs):
        guest_past_visits = []
        get_guest_cnic = kwargs.get('guest_cnic_input')

        if get_guest_cnic:
            visits = request.env['guest.history'].sudo().search([('guest_cnic', '=', int(get_guest_cnic))])
            print('Guest Name: ', visits)
            for visit in visits:
                guest_past_visits.append({
                    'guest_name': visit.guest_name,
                    'date_ordered': visit.date_ordered.strftime('%Y-%m-%d'),
                    'guest_cnic': visit.guest_cnic,
                    'check_out_date': visit.check_out_date.strftime('%Y-%m-%d'),
                    'stay_days': visit.stay_days,
                    'price': visit.price,
                    'room_number': visit.room_number if visit.room_number else "N/A",
                })
            return request.render('hotel_management.hotel_guest_history', {'guest_past_visits': guest_past_visits})

        return request.render('hotel_management.guest_history_main_page', {
            'guest_past_visits': guest_past_visits
        })


class HotelRoomDetails(http.Controller):
    @http.route('/hotel/available_rooms', type='http', auth='public', website=True)
    def get_available_rooms(self):
        available_room_details = []
        avail_rooms = request.env['hotel.room'].search([('state', '=', 'draft')])

        for room in avail_rooms:
            room_image = room.room_image
            # If room_image is not empty and is a bytes object, decode it to string
            if room_image and isinstance(room_image, bytes):
                room_image = room_image.decode('utf-8')

            available_room_details.append({
                'room_seq_no': room.name,
                'room_name': room.room_type_id.room_type or '',
                'room_ac_facility': room.ac_facility or False,
                'room_heater_facility': room.heater_facility or False,
                'room_gym_facility': room.gym_facility or False,
                'room_price_single_day': room.room_price or False,
                'room_image': room_image or False,
            })

        return request.render('hotel_management.room_details_view', {
            'available_room_details': available_room_details
        })
