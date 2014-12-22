#!/usr/bin/env python

from heat.engine import resource
from heat.openstack.common.gettextutils import _
from heat.openstack.common import log as logging
from urllib2 import Request,urlopen, URLError

import acitoolkit.acisession
import acitoolkit.acitoolkit as ACI

import json

import cobra.mit.access
import cobra.mit.session
import cobra.mit.request
import cobra.model.fv


logger = logging.getLogger(__name__)


class APIC(resource.Resource):

    properties_schema = {
        'Hostname': {
            'Type': 'String',
            'Default': '',
            'Description': _('Hostname of the APIC Controller')
        },
        'User': {
            'Type': 'String',
            'Default': '',
            'Description': _('Username')
        },
        'Password': {
            'Type': 'String',
            'Default': '',
            'Description': _('APIC Password')
        },
        'Target': {
            'Type': 'String',
            'Default': '',

        },
        'Data': {
            'Type': 'String',
            'Default': '',
            'Description': _('JSON or XML data')
        }

    }

    attributes_schema = {
        'Name': _('Name'),
        'Response': _('APIC Response'),
        'AuthStatusCode': _('APIC Authentication Status'),
    }

    def _resolve_attribute(self, name):
        if name == 'Name':
            return self.physical_resource_name()
        elif name == 'Response':
            return self.resource_id
        elif name == 'AuthStatusCode':
            return self.apic_attributes['AuthStatusCode']
        else:
            raise ValueError('No Valid Attribute %s' % name)


    def __init__(self, *args, **kwargs):
        super(APIC, self).__init__(*args, **kwargs)

        ## integrate acitoolkit
        self.apic_attributes = {}
        args = {
            'Hostname': self.properties['Hostname'],
            'User': self.properties['User'],
            'Password': self.properties['Password'],
            'Target': self.properties['Target'],
            'Data': self.properties['Data'],
        }
        self._apic_session = acitoolkit.acisession.Session('http://'+args['Hostname'], args['User'], args['Password'])
        resp = self._apic_session.login()
        self.apic_attributes['AuthStatusCode'] = resp.status_code

    def authenticate(self,host,user,passwd):
        ls = cobra.mit.session.LoginSession('http://'+host,user,passwd)
        md = cobra.mit.access.MoDirectory(ls)
        md.login()
        return md

    def handle_create(self):
        args = {
            'Hostname': self.properties['Hostname'],
            'User': self.properties['User'],
            'Password': self.properties['Password'],
            'Target': self.properties['Target'],
            'Data': self.properties['Data'],
        }

        md = self.authenticate(args['Hostname'], args['User'], args['Password'])
        topMo = md.lookupByDn(args['Target'])
        fvTenant = cobra.model.fv.Tenant(topMo, name='test2')
        self.resource_id_set(fvTenant.dn)
        #self.apic_attributes['Tenants'] = ACI.Tenant.get(self._apic_session)

        c = cobra.mit.request.ConfigRequest()
        c.addMo(topMo)
        md.commit(c)




    def handle_delete(self):
        pass

    def handle_suspend(self):
        pass


def resource_mapping():
    return {
        'OS::Heat::APIC': APIC
    }


