# -*- coding: utf-8 -*-

from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
#from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.osv import expression


class CustomerPortalCt(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortalCt, self)._prepare_portal_layout_values()
        CT = request.env['x_ctratamientos']
        ct_count = CT.search_count([])
        order_count = CT.search_count([])

        values.update({
            'ct_count': ct_count,
            'order_count': order_count,
        })
        return values

    @http.route(['/my/cts', '/my/cts/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_cts(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        CT = request.env['x_ctratamientos']

        domain = [
         
        ]

        searchbar_sortings = {
            'date': {'label': _('Order Date'), 'order': 'create_date desc'},
            'name': {'label': _('Reference'), 'order': 'x_name'},
            'stage': {'label': _('Stage'), 'order': 'x_estado'},
        }

        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('x_ctratamientos', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        ct_count = CT.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/cts",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=ct_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        cts = CT.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_quotations_history'] = cts.ids[:100]

        values.update({
            'date': date_begin,
            'cts': cts.sudo(),
            'page_name': 'ct',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/cts',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("portal_green_crm.portal_my_cts", values)
    
    
    #### V11 ###########
    
    def _ct_check_access(self, ct_id, access_token=None):
        ct = request.env['x_ctratamientos'].browse([ct_id])
        ct_sudo = ct.sudo()
        try:
            ct.check_access_rights('read')
            ct.check_access_rule('read')
        except AccessError:
            if not access_token or not consteq(ct_sudo.access_token, access_token):
                raise
        return ct_sudo
    
    def _ct_get_page_view_values(self, ct, access_token, **kwargs):
        
        values = {
            'ct': ct,
        }
        if access_token:
            values['no_breadcrumbs'] = True
            values['access_token'] = access_token
        #values['portal_confirmation'] = ct.get_portal_confirmation_action()

        if kwargs.get('error'):
            values['error'] = kwargs['error']
        if kwargs.get('warning'):
            values['warning'] = kwargs['warning']
        if kwargs.get('success'):
            values['success'] = kwargs['success']

        history = request.session.get('my_ct_history', [])
        values.update(get_records_pager(history, ct))

        return values
    
    @http.route(['/my/cts/<int:ct>'], type='http', auth="public", website=True)
    def portal_ct_page(self, ct=None, access_token=None, **kw):
        try:
            ct_sudo = self._ct_check_access(ct, access_token=access_token)
        except AccessError:
            return request.redirect('/my')

        values = self._ct_get_page_view_values(ct_sudo, access_token, **kw)
        return request.render("portal_green_crm.portal_ct_page", values)

    @http.route(['/my/cts/pdf/<int:ct_id>'], type='http', auth="public", website=True)
    def portal_ct_report(self, ct_id, access_token=None, **kw):
        try:
            ct_sudo = self._ct_check_access(ct_id, access_token)
        except AccessError:
            return request.redirect('/my')
        # print report as sudo, since it require access to taxes, payment term, ... and portal
        # does not have those access rights.
        pdf = request.env.ref('studio_customization.cto_tratamientos_rep_efa32e8d-9052-4a6b-b184-604ee4b5fcbc').sudo().render_qweb_pdf([ct_sudo.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)