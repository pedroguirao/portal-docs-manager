# -*- coding: utf-8 -*-

from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
#from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.osv import expression


class CustomerPortalNt(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortalNt, self)._prepare_portal_layout_values()
        NT = request.env['x_nts']
        nt_count = NT.search_count([])
        order_count = NT.search_count([])
        
        values.update({
            'nt_count': nt_count,
            'order_count': order_count,
        })
        return values
    
    @http.route(['/my/nts', '/my/nts/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_nts(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        NT = request.env['x_nts']

        domain = []

        searchbar_sortings = {
            'date': {'label': _('Order Date'), 'order': 'create_date'},
            'name': {'label': _('Reference'), 'order': 'x_name'},
            'stage': {'label': _('Stage'), 'order': 'x_estado'},
        }

        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('x_nts', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        nt_count = NT.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/nts",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=nt_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        nts = NT.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_quotations_history'] = nts.ids[:100]

        values.update({
            'date': date_begin,
            'nts': nts.sudo(),
            'page_name': 'nt',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/nts',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("portal_green_crm.portal_my_nts", values)
    
    
    #### V11 ###########
    
    def _nt_check_access(self, nt_id, access_token=None):
        nt = request.env['x_nts'].browse([nt_id])
        nt_sudo = nt.sudo()
        try:
            nt.check_access_rights('read')
            nt.check_access_rule('read')
        except AccessError:
            if not access_token or not consteq(nt_sudo.access_token, access_token):
                raise
        return nt_sudo
    
    def _nt_get_page_view_values(self, nt, access_token, **kwargs):
        
        values = {
            'nt': nt,
        }
        if access_token:
            values['no_breadcrumbs'] = True
            values['access_token'] = access_token
        #values['portal_confirmation'] = nt.get_portal_confirmation_action()

        if kwargs.get('error'):
            values['error'] = kwargs['error']
        if kwargs.get('warning'):
            values['warning'] = kwargs['warning']
        if kwargs.get('success'):
            values['success'] = kwargs['success']

        history = request.session.get('my_nt_history', [])
        values.update(get_records_pager(history, nt))

        return values
    
    @http.route(['/my/nts/<int:nt>'], type='http', auth="public", website=True)
    def portal_nt_page(self, nt=None, access_token=None, **kw):
        try:
            nt_sudo = self._nt_check_access(nt, access_token=access_token)
        except AccessError:
            return request.redirect('/my')

        values = self._nt_get_page_view_values(nt_sudo, access_token, **kw)
        return request.render("portal_green_crm.portal_nt_page", values)

    @http.route(['/my/nts/pdf/<int:nt_id>'], type='http', auth="public", website=True)
    def portal_nt_report(self, nt_id, access_token=None, **kw):
        try:
            nt_sudo = self._nt_check_access(nt_id, access_token)
        except AccessError:
            return request.redirect('/my')
        # print report as sudo, since it require access to taxes, payment term, ... and portal
        # does not have those access rights.
        pdf = request.env.ref('studio_customization.notificaciones_de_tr_5f9525dc-164d-467e-8819-eceaf852ee1b').sudo().render_qweb_pdf([nt_sudo.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

    