#!/usr/bin/env python

#
# XML atribute elements extension for Portuguese SAML Implementation
# By micael-grilo 
#

from saml2 import SamlBase

NAMESPACE = 'http://autenticacao.cartaodecidadao.pt/atributos'

class FAAALevel(SamlBase):
    """The http://autenticacao.cartaodecidadao.pt/atributos:FAALevel element """

    c_tag = 'FAAALevel'
    c_namespace = NAMESPACE
    c_children = SamlBase.c_children.copy()
    c_attributes = SamlBase.c_attributes.copy()
    c_child_order = SamlBase.c_child_order[:]
    c_cardinality = SamlBase.c_cardinality.copy()
    c_attributes['publisher'] = ('publisher', 'string', True)
    c_attributes['creationInstant'] = ('creation_instant', 'dateTime', False)
    c_attributes['publicationId'] = ('publication_id', 'string', False)

    def __init__(self,
                 publisher=None,
                 creation_instant=None,
                 publication_id=None,
                 text=None,
                 extension_elements=None,
                 extension_attributes=None):
        SamlBase.__init__(self,
                          text=text,
                          extension_elements=extension_elements,
                          extension_attributes=extension_attributes)
        self.publisher = publisher
        self.creation_instant = creation_instant
        self.publication_id = publication_id



class LogoutUrl(SamlBase):
    c_tag = 'LogoutUrl'
    c_namespace = 'http://autenticacao.cartaodecidadao.pt/logout'
