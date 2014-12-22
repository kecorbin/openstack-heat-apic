#!/usr/bin/env python

from heat.engine import resource
from heat.openstack.common.gettextutils import _
from heat.openstack.common import log as logging
import acitoolkit.acisession
import acitoolkit.acitoolkit as ACI


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
        'ToolkitMethod': {
            'Type': 'String',
            'Default': '',
            'Description': _('Toolkit Method to use')
        },
        'ToolkitData': {
            'Type': 'String',
            'Default': '',
            'Description': _('Data for ToolkitMethod')
        },
        'RawJSON': {
            'Type': 'List',
            'Default': '',
            'Description': _('URL , JSON Data to post')
        },

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
        }
        self._apic_session = acitoolkit.acisession.Session('http://'+args['Hostname'], args['User'], args['Password'])
        resp = self._apic_session.login()
        self.apic_attributes['AuthStatusCode'] = resp.status_code

    def _build_object(self, method, data):
        if method == 'Tenant':
            obj = ACI.Tenant(str(data))
            resp = self._apic_session.push_to_apic(obj.get_url(), obj.get_json())
            self.resource_id_set(resp.text)

        elif method == 'raw':
            url = self.properties['RawJSON'][0]
            data = self.properties['RawJSON'][1]
            self._apic_session.push_to_apic(url, data)

        else:
            raise ValueError('%s is not defined as a method of ACI' % method)

    def handle_create(self):
        method = self.properties['ToolkitMethod']
        data = self.properties['ToolkitData']
        self._build_object(method, data)

    def handle_delete(self):
        pass

    def handle_suspend(self):
        pass


def resource_mapping():
    return {
        'OS::Heat::APIC': APIC
    }
