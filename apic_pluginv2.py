#!/usr/bin/env python

from heat.engine import resource
from heat.openstack.common.gettextutils import _
from heat.openstack.common import log as logging
import cobra.mit.access
import cobra.mit.session
import cobra.mit.request
import cobra.model.fv
import httplib

httplib.HTTPConnection.debuglevel = 1

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
    }

    def __init__(self, *args, **kwargs):
        super(APIC, self).__init__(*args, **kwargs)
        a = self.physical_resource_name
        #self._client_class = kwargs.get('client_class', docker.Client)
        self.response = 'None2'

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
        c = cobra.mit.request.ConfigRequest()
        c.addMo(topMo)
        md.commit(c)

    def _resolve_attribute(self, name):
        if name == 'Name':
            return self.physical_resource_name()
        elif name == 'Response':
            return self.resource_id
        else:
            raise ValueError('No Valid Attribute %s' % name)


    def handle_delete(self):
        pass

    def handle_suspend(self):
        pass


def resource_mapping():
    return {
        'OS::Heat::APIC': APIC
    }


