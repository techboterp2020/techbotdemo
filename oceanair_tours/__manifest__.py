{
    'name': 'OceanAir Tours – Booking, Costing & Profitability',
    'version': '19.0.1.0.0',
    'category': 'Services/Tours',
    'summary': 'Tour booking, supplier costing automation, one-click invoicing '
               'and tour profitability for OceanAir Travels (Al Salah Group).',
    'description': """
OceanAir Tours
==============
End-to-end Tour Operations workflow demo for Odoo 19 Enterprise:

* Tour packages catalog (City, Safari, Egypt, Croatia, Domes, Custom)
* Central Booking record: customer, pax, dates, sales agent
* Supplier cost lines (hotel / transport / guide / tickets / visa ...)
* Automatic margin & profitability calculation
* One-click customer invoice (Booking -> Accounting)
* Auto-generated vendor bills grouped by supplier
* CRM: convert an Opportunity into a Tour Booking
* Cost-center (analytic) tagging
* Pivot / Graph profitability reporting + printable Costing Sheet
""",
    'author': 'OceanAir Travels',
    'website': 'https://www.oceanairtravels.com',
    'depends': ['mail', 'account', 'crm'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/product_data.xml',
        'views/tour_package_views.xml',
        'views/tour_booking_views.xml',
        'views/crm_lead_views.xml',
        'report/tour_booking_report.xml',
        'views/menus.xml',
        'data/sample_data.xml',
    ],
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
