# -*- coding: utf-8 -*-

from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
#from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.osv import expression


class CustomerPortalAu(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortalAu, self)._prepare_portal_layout_values()
        Autorizaciones = request.env['x_autorizaciones']
        autorizaciones_count = Autorizaciones.search_count([])
        order_count = Autorizaciones.search_count([])
            
        values.update({
            'order_count': order_count,
            'autorizaciones_count': autorizaciones_count,
        })
        return values
    @http.route(['/my/autorizaciones', '/my/aus/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_aus(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        Autorizaciones = request.env['x_autorizaciones']

        domain = []

        searchbar_sortings = {
            'date': {'label': _('Order Date'), 'order': 'x_finicio desc'},
            'name': {'label': _('Reference'), 'order': 'x_name'},
            'stage': {'label': _('Stage'), 'order': 'x_estado'},
        }

        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('x_autorizaciones', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        autorizaciones_count = Autorizaciones.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/aus",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=autorizaciones_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        aus = Autorizaciones.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_quotations_history'] = aus.ids[:100]

        values.update({
            'date': date_begin,
            'aus': aus.sudo(),
            'page_name': 'au',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/aus',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("portal_green_crm.portal_my_aus", values)
    
    
    #### V11 ###########
    
    def _au_check_access(self, au_id, access_token=None):
        au = request.env['x_autorizaciones'].browse([au_id])
        au_sudo = au.sudo()
        try:
            au.check_access_rights('read')
            au.check_access_rule('read')
        except AccessError:
            if not access_token or not consteq(au_sudo.access_token, access_token):
                raise
        return au_sudo
    
    def _au_get_page_view_values(self, au, access_token, **kwargs):
        
        values = {
            'au': au,
        }
        if access_token:
            values['no_breadcrumbs'] = True
            values['access_token'] = access_token
        #values['portal_confirmation'] = au.get_portal_confirmation_action()

        if kwargs.get('error'):
            values['error'] = kwargs['error']
        if kwargs.get('warning'):
            values['warning'] = kwargs['warning']
        if kwargs.get('success'):
            values['success'] = kwargs['success']

        history = request.session.get('my_au_history', [])
        values.update(get_records_pager(history, au))

        return values
    
    @http.route(['/my/aus/<int:au>'], type='http', auth="public", website=True)
    def portal_au_page(self, au=None, access_token=None, **kw):
        try:
            au_sudo = self._au_check_access(au, access_token=access_token)
        except AccessError:
            return request.redirect('/my')

        values = self._au_get_page_view_values(au_sudo, access_token, **kw)
        return request.render("portal_green_crm.portal_au_page", values)

    @http.route(['/my/aus/pdf/<int:au_id>'], type='http', auth="public", website=True)
    def portal_au_report(self, au_id, access_token=None, **kw):
        try:
            au_sudo = self._au_check_access(au_id, access_token)
        except AccessError:
            return request.redirect('/my')
        # print report as sudo, since it require access to taxes, payment term, ... and portal
        # does not have those access rights.
        pdf = request.env.ref('studio_customization.autorizaciones_repor_4107c771-84a7-456e-b0ad-7fabb6f1544c').sudo().render_qweb_pdf([au_sudo.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

   
