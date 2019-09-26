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

        Partes = request.env['account.analytic.line']
        partes_count = Partes.search_count([
            ('x_firmado_id', '!=', False),
           
        ])
        values.update({
            'partes_count': partes_count,
        })
        return values

    @http.route(['/my/partes', '/my/partes/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_partes(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        cuestionario = request.env['x_cuestionarios']

        domain = [
            ('x_tipo_ids', '!=', ['False']),
        ]

        searchbar_sortings = {
            
            'name': {'label': _('Reference'), 'cuestionario': 'x_name'},
           
        }

        # default sortby order
        if not sortby:
            sortby = 'name'
        sort_order = searchbar_sortings[sortby]['cuestionario']

        archive_groups = self._get_archive_groups('x_cuestinarios', domain)
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
        request.session['my_cuestionarios_history'] = dis.ids[:100]

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
        return request.render("portal_cuestionarioss.portal_my_home_cuestionarios", values)
    
    
    @http.route(['/my/partes/<int:parte_id>'], type='http', auth="public", website=True)
    def portal_parte_page(self, cuestionario_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            cuestionario_sudo = self._document_check_access('x_cuestionarios', cuestionario_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=cuestionario_sudo, report_type=report_type, report_ref='sale.action_report_saleorder', download=download)

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        now = fields.Date.today()

        history = request.session.get('my_cuestionarios_history', [])
        values.update(get_records_pager(history, cuestionario_sudo))

        return request.render('portal_cuestionarios.cuestionarios_portal_template', values)