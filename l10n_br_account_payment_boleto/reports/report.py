# -*- coding: utf-8 -*-
##############################################################################
#
#    Account Payment Boleto module for Odoo
#    Copyright (C) 2012-2015 KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Miléo <mileo@kmee.com.br>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from __future__ import with_statement
from openerp.report.render import render
from openerp.report.interface import report_int
from openerp import pooler
from ..boleto.document import Boleto
from openerp.osv import osv
import base64
from openerp.tools.translate import _
from openerp.exceptions import Warning as UserError


class external_pdf(render):

    def __init__(self, pdf):
        render.__init__(self)
        self.pdf = pdf
        self.output_type = 'pdf'

    def _render(self):
        return self.pdf


class report_custom(report_int):
    """
        Custom report for return boletos
    """

    def create(self, cr, uid, ids, datas, context=False):
        if not context:
            context = {}
        active_ids = context.get('active_ids')
        active_model = context.get('active_model')
        pool = pooler.get_pool(cr.dbname)
        ids_move_lines = []
        if not active_model:
            active_model =  context.get('default_model')
        aml_obj = pool.get('account.move.line')
        if active_model == 'account.invoice':
            ai_obj = pool.get('account.invoice')
            # this case happens when we open wizard to send email and change template in "Use template" field
            if not active_ids:
                if context.get('active_id'):
                    active_ids = [context.get('active_id')]
                if not active_ids and context.get('default_res_id'):
                    active_ids = [context.get('default_res_id')]
                context.update({'boleto_no_attachment' : True})
            for account_invoice in ai_obj.browse(cr, uid, active_ids):
                ids_move_lines_attach = []
                for move_line in account_invoice.move_line_receivable_id:
                    ids_move_lines.append(move_line.id)
                    ids_move_lines_attach.append(move_line.id)

                # generate separate report for each invoice to attach
                if len(ids_move_lines_attach) and not context.get('boleto_no_attachment',False):
                    boleto_list = aml_obj.send_payment(
                        cr, uid, ids_move_lines_attach)
                    pdf_string_attach = Boleto.get_pdfs(boleto_list)
                    file_name = "INV-%s-boleto.pdf" % account_invoice.move_id.name
                    attach_vals = {
                        'name': file_name,
                        'datas_fname': file_name,
                        'datas': base64.b64encode(pdf_string_attach),
                        'res_model': 'account.invoice',
                        'res_id': account_invoice.id,
                    }
                    pool.get('ir.attachment').create(cr, uid, attach_vals)
            if not len(ids_move_lines):
                raise UserError(_(
                    "No receivable or payable move lines found. Please set Gera Financeiro to True in Journal"))
        elif active_model == 'account.move.line':
            ids_move_lines = active_ids
        else:
            return False

        boleto_list = aml_obj.send_payment(cr, uid, ids_move_lines)
        if not boleto_list:
            raise osv.except_osv(
                'Error !', ('Não é possível gerar os boletos\n'
                            'Certifique-se que a fatura esteja confirmada e o '
                            'forma de pagamento seja duplicatas'))
        pdf_string = Boleto.get_pdfs(boleto_list)
        self.obj = external_pdf(pdf_string)
        self.obj.render()
        return self.obj.pdf, 'pdf'


report_custom('report.l10n_br_account_payment_boleto.report')
