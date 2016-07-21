# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import models, fields


class ResPartnerBank(models.Model):
    """ Adiciona campos necessários para o cadastramentos de contas
    bancárias no Brasil."""
    _inherit = 'res.partner.bank'

    codigo_da_empresa = fields.Char(
        u'Código da empresa', size=20,
        help=u"Será informado pelo banco depois do cadastro do beneficiário "
             u"na agência")
