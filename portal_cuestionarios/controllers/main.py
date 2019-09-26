# -*- coding: utf-8 -*-

from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.osv import expression


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        Cuestionarios = request.env['x_cuestionarios']
        cuestionarios_count = Cuestionarios.search_count([
            ('x_visible_portal', '!=', False),
           
        ])
        values.update({
            'cuestionarios_count': cuestionarios_count,
        })
        return values

    @http.route(['/my/cuestionarios', '/my/cuestionarios/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_cuestionarios(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        cuestionario = request.env['x_cuestionarios']

        domain = [
            ('x_visible_portal', '=', True),
        ]

        searchbar_sortings = {
            
            'name': {'label': _('Reference'), 'cuestionario': 'x_name'},
           
        }

        # default sortby order
        if not sortby:
            sortby = 'name'
        sort_order = searchbar_sortings[sortby]['cuestionario']

        archive_groups = self._get_archive_groups('x_cuestionarios', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        cuestionario_count = cuestionario.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/cuestionarios",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=cuestionario_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        cuestionarios = cuestionario.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_cuestionarios_history'] = cuestionarios.ids[:100]

        values.update({
            'date': date_begin,
            'cuestionarios': cuestionarios.sudo(),
            'page_name': 'cuestionario',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/cuestionarios',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("portal_cuestionarios.portal_my_cuestionarios", values)
    
    
    @http.route(['/my/cuestionario/<int:cuestionario_id>'], type='http', auth="public", website=True)
    def portal_cuestionario_page(self, cuestionario_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            cuestionario_sudo = self._document_check_access('x_cuestionarios', cuestionario_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=cuestionario_sudo, report_type=report_type, report_ref='sale.action_report_saleorder', download=download)

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        now = fields.Date.today()
        
        values = {
            'cuestionario': cuestionario_sudo,
            'message': message,
            'token': access_token,
            'bootstrap_formatting': True,
            'report_type': 'html',
        }
        
        history = request.session.get('my_cuestionarios_history', [])
        values.update(get_records_pager(history, cuestionario_sudo))

        return request.render('portal_cuestionarios.cuestionarios_portal_template', values)
    
    def _cuestionario_check_access(self, cuestionario_id, access_token=None):
        cuestionario = request.env['x_cuestionarios'].browse([cuestionario_id])
        cuestionario_sudo = cuestionario.sudo()
        #try:
        #    order.check_access_rights('read')
        #    order.check_access_rule('read')
        #except AccessError:
        #    if not access_token or not consteq(order_sudo.access_token, access_token):
        #        raise
        return cuestionario_sudo
    
    @http.route(['/my/cuestionario/pdf/<int:cuestionario_id>'], type='http', auth="public", website=True)
    def portal_cuestionario_report(self, cuestionario_id, access_token=None, **kw):
        try:
            cuestionario_sudo = self._cuestionario_check_access(cuestionario_id, access_token)
        except AccessError:
            return request.redirect('/my')

        # print report as sudo, since it require access to taxes, payment term, ... and portal
        # does not have those access rights.
        pdf = request.env.ref(
            'portal_cuestionarios.action_report_cuestionarios').sudo().render_qweb_pdf([cuestionario_sudo.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

    