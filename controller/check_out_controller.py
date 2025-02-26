from odoo import http, fields
from odoo.addons.base.models.ir_actions_report import available
from odoo.exceptions import ValidationError
from odoo.http import request


class CheckOutController(http.Controller):
    @http.route('/check/out', type='http', auth='user', website=True)
    def check_out(self, **post):
        guests_id = request.env['hotel.base'].search([('state', '=', 'done')])
        print([(x.name, x.guest_name, x.room_number.room_type_id.room_type) for x in guests_id])
        guests = []
        for guest in guests_id:
            guests.append({
                'guest_id': guest.id,  # Use ID instead of name
                'guest_name': guest.guest_name,
                'guest_room': guest.room_number.room_type_id.room_type,
                'display_name': f'{guest.guest_name}  -  {guest.room_number.room_type_id.room_type}',
            })

        if post:
            get_display_name = post.get('guest_name')
            selected_guest = next((g for g in guests if g['display_name'] == get_display_name), None)

            if selected_guest:
                guest_id = selected_guest['guest_id']
                print(f"Guest ID: {guest_id}")

                approval_check_out_id = request.env['approval.check.out'].create({
                    'display_name': get_display_name,
                    'guest_id': guest_id,
                })
                print(f"Out ID: {approval_check_out_id}")
                print(approval_check_out_id.display_name)
                print(approval_check_out_id.guest_id)
                print(approval_check_out_id.guest_seq)
                print(approval_check_out_id.guest_name)
                print(approval_check_out_id.guest_room)

                return request.render('hotel_management.room_checked_out_requested_success')

        # if post:
        #     get_display_name = post.get('guest_name')
        #
        #     # Find the matching guest by display_name
        #     selected_guest = next((g for g in guests if g['display_name'] == get_display_name), None)
        #
        #     if selected_guest:
        #         guest_id = selected_guest['guest_id']  # Using ID now
        #         print(f"Guest ID: {guest_id}")
        #
        #         del_obj = request.env['hotel.base'].browse(guest_id)
        #         if del_obj:
        #             print(f'Record: {del_obj} found for deletion')
        #
        #             # Reset Room Status
        #             if del_obj.room_number:
        #                 del_obj.room_number.button_reset()
        #
        #             # Unlink the record to delete it
        #             # del_obj.unlink()
        #             print(f'Record: {del_obj} has been deleted')
        #
        #             return request.render('hotel_management.room_checked_out_success_view')

        return request.render("hotel_management.hotel_check_out_form", {
            'guests': guests,
        })


class ApproveCheckOut(http.Controller):
    @http.route('/approve/check/out', type='http', auth='user', website=True)
    def approve_checkout(self, **post):
        check_out_reqs_list = []
        check_out_reqs = request.env['approval.check.out'].search([])
        for out in check_out_reqs:
            check_out_reqs_list.append({
                'display_name': f'{out.guest_seq}  -  {out.guest_name}',
            })
        print(check_out_reqs_list)

        if post:
            get_display_name = post.get('guest_name_seq_out')
            print(get_display_name)
            if get_display_name:
                split = get_display_name.split('-')
                print(split, '::::')
                zero_inx = split[0].split(' ')
                fst_inx = split[1].split(' ')
                guest_seq = zero_inx[0]
                guest_name = fst_inx[2]

                #deleting rec in approval check out.
                search_approve_check_out = request.env['approval.check.out'].search([('guest_id', '=', guest_seq)])
                search_approve_check_out.sudo().unlink()

                del_obj = request.env['hotel.base'].search([('name', '=', guest_seq)])
                if del_obj:
                    print(f'Record: {del_obj} found for deletion')
                    if del_obj.room_number:
                        del_obj.room_number.button_reset()
                        return request.render('hotel_management.room_checked_out_success_view')

        return request.render("hotel_management.hotel_check_out_approval", {'check_out_reqs_list': check_out_reqs_list})
