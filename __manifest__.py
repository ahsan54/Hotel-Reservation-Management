{
    'name': 'Hotel Management',
    'author': 'Ahsan',
    'description': """Comprehensive hotel management system in Odoo.""",
    'version': '18.0.1.2',  # Incremented for clarity
    'summary': 'Complete Hotel Management Solution for Odoo',
    'sequence': 1,
    'category': 'Services/Hotel',
    'website': 'https://www.google.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr',
        'website',
        'portal',
        'sale','account','account_accountant'
    ],
    'installable': True,
    'application': True,  # Set to True for easy access in the Apps menu
    'auto_install': False,
    'assets': {
        'web.assets_backend': [
            'hotel_management/static/src/css/style.css',
            # '/hotel_management/static/src/css/dashboard_style.css',

        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'security/groups.xml',
        'views/menu_ids_view.xml',
        'views/dashboard_controller_view.xml',
        'views/room_details_controller.xml',
        'views/guest_history_controller.xml',
        'views/approval_check_in_controller.xml',
        'views/approval_check_out_controller.xml',
        'views/check_in_controller_view.xml',
        'views/check_out_controller_view.xml',
        'views/request_check_in_view.xml',
        'views/room_creation_view.xml',
        'views/logs_room_booked_view.xml',
        'views/request_check_out_view.xml',
        'views/room_type_view.xml',
        'views/guest_history_views.xml',
    ],
}
