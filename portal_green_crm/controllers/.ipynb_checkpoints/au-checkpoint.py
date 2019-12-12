# -*- coding: utf-8 -*-

from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
#from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.osv import expression


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        DI = request.env['x_dis']
        di_count = DI.search_count([])
        #order_count = DI.search_count([])
        CT = request.env['x_ctratamientos']
        ct_count = CT.search_count([])
        #order_count = CT.search_count([])
        NT = request.env['x_nts']
        nt_count = NT.search_count([])
        Autorizaciones = request.env['x_autorizaciones']
        autorizaciones_count = Autorizaciones.search_count([])
        
        values.update({
            'di_count': di_count,
            'ct_count': ct_count,
            'nt_count': nt_count,
            'autorizaciones_count': autorizaciones_count,
        })
        return values

    @http.route(['/my/dis', '/my/dis/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_dis(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        user_id = request.env.user.user_id
        print(partner)
        print(user_id)
        DI = request.env['x_dis']

        domain = [
            #('x_estado', 'in', ['pendiente']),
        ]

        searchbar_sortings = {
            'date': {'label': _('Order Date'), 'order': 'x_fdi_inicio_id desc'},
            'name': {'label': _('Reference'), 'order': 'x_name'},
            'stage': {'label': _('Stage'), 'order': 'x_estado'},
        }

        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('x_dis', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        di_count = DI.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/dis",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=di_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        dis = DI.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_quotations_history'] = dis.ids[:100]

        values.update({
            'date': date_begin,
            'dis': dis.sudo(),
            'page_name': 'di',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/dis',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("portal_dis.portal_my_dis", values)
    
    
    #### V11 ###########
    
    def _di_check_access(self, di_id, access_token=None):
        di = request.env['x_dis'].browse([di_id])
        di_sudo = di.sudo()
        try:
            di.check_access_rights('read')
            di.check_access_rule('read')
        except AccessError:
            if not access_token or not consteq(di_sudo.access_token, access_token):
                raise
        return di_sudo
    
    def _di_get_page_view_values(self, di, access_token, **kwargs):
        
        values = {
            'di': di,
        }
        if access_token:
            values['no_breadcrumbs'] = True
            values['access_token'] = access_token
        #values['portal_confirmation'] = di.get_portal_confirmation_action()

        if kwargs.get('error'):
            values['error'] = kwargs['error']
        if kwargs.get('warning'):
            values['warning'] = kwargs['warning']
        if kwargs.get('success'):
            values['success'] = kwargs['success']

        history = request.session.get('my_di_history', [])
        values.update(get_records_pager(history, di))

        return values
    
    @http.route(['/my/dis/<int:di>'], type='http', auth="public", website=True)
    def portal_di_page(self, di=None, access_token=None, **kw):
        try:
            di_sudo = self._di_check_access(di, access_token=access_token)
        except AccessError:
            return request.redirect('/my')

        values = self._di_get_page_view_values(di_sudo, access_token, **kw)
        return request.render("portal_dis.portal_di_page", values)

    @http.route(['/my/dis/pdf/<int:di_id>'], type='http', auth="public", website=True)
    def portal_di_report(self, di_id, access_token=None, **kw):
        try:
            di_sudo = self._di_check_access(di_id, access_token)
        except AccessError:
            return request.redirect('/my')
        # print report as sudo, since it require access to taxes, payment term, ... and portal
        # does not have those access rights.
        pdf = request.env.ref('studio_customization.report_9ff70961-9b77-435c-969e-64439fb6b04f').sudo().render_qweb_pdf([di_sudo.id])[0]
        #pdf = request.env.ref('sale.action_report_saleorder').sudo().render_qweb_pdf([di_sudo.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)