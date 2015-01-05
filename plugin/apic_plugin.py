#!/usr/bin/env python

from heat.engine import resource
from heat.openstack.common.gettextutils import _
from heat.openstack.common import log as logging
import acitoolkit.acisession
import acitoolkit.acitoolkit as ACI
import iniparse
logger = logging.getLogger(__name__)

from oslo.config import cfg
plugin_opts = [
    cfg.StrOpt('apic_host',
               default='apic_host',
               help='apic_host'),
    cfg.StrOpt('apic_username',
               default='apic_username',
               help='apic_username'),
    cfg.StrOpt('apic_password',
               default='apic_password',
               help='apic_password'),
    cfg.StrOpt('apic_system_id',
               default='_openstack',
               help='apic_system_id'),
]

conf = 'heat.common.config'
apic_optgroup = cfg.OptGroup(name='apic_plugin', title='options for the apic plugin')
cfg.CONF.register_group(apic_optgroup)
cfg.CONF.register_opts(plugin_opts, apic_optgroup)
cfg.CONF.import_group(apic_optgroup, conf)

class APIC(resource.Resource):

    properties_schema = {
        'Project': {
            'Type': 'String',
            'Default': '',
            'Description': _('Project Name')
        },
        'Network': {
            'Type': 'String',
            'Default': '',
            'Description': _('Network Name')
        },
        'Contract': {
            'Type': 'String',
            'Default': '',
            'Description': _('Network Name')
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
        'Body': _('Body of request'),
        'Status': _('Status Code of Request'),
    }

    def __init__(self, *args, **kwargs):
        super(APIC, self).__init__(*args, **kwargs)
        ## integrate acitoolkit
        self.apic_attributes = {}
        host = cfg.CONF.apic_plugin.apic_host
        username = cfg.CONF.apic_plugin.apic_username
        password = cfg.CONF.apic_plugin.apic_password
        self.apic_system_id = cfg.CONF.apic_plugin.apic_system_id
        self._apic_session = acitoolkit.acisession.Session('http://'+host, username, password)
        resp = self._apic_session.login()
        self.apic_attributes['AuthStatusCode'] = resp.status_code


    def _resolve_attribute(self, name):
        if name == 'Name':
            return self.physical_resource_name()
        elif name == 'Response':
            return self.resource_id
        elif name == 'AuthStatusCode':
            return self.apic_attributes['AuthStatusCode']
        elif name == 'Status':
            return self.apic_attributes['Status']
        else:
            raise ValueError('No Valid Attribute %s' % name)


    def _build_object(self, method, data):
        if method == 'Tenant':
            obj = ACI.Tenant(str(data))
            resp = self._apic_session.push_to_apic(obj.get_url(), obj.get_json())
            self.resource_id_set(resp.request.body)

        elif method == 'ConsumeContract':
            tenant = self.properties['Project']
            epg = self.properties['Network']
            contract = self.properties['Contract']
            url = '/api/node/mo/uni/tn-_%s_%s/ap-%s_app/epg-%s.json' \
                  % (self.apic_system_id,tenant,self.apic_system_id,epg)
            data = {"fvRsCons":{"attributes":{"tnVzBrCPName": contract,"status":"created"},"children":[]}}
            resp = self._apic_session.push_to_apic(url, data)
            self.resource_id_set(resp.request.body)
            self.apic_attributes['Status'] = resp.status_code

        elif method == 'ProvideContract':
            tenant = self.properties['Project']
            epg = self.properties['Network']
            contract = self.properties['Contract']
            url = '/api/node/mo/uni/tn-_%s_%s/ap-%s_app/epg-%s.json' \
                  % (self.apic_system_id,tenant,self.apic_system_id,epg)
            data = {"fvRsProv":{"attributes":{"tnVzBrCPName": contract,"status":"created"},"children":[]}}
            resp = self._apic_session.push_to_apic(url, data)
            self.resource_id_set(resp.request.body)
            self.apic_attributes['Status'] = resp.status_code

        elif method == 'raw':
            url = self.properties['RawJSON'][0]
            data = self.properties['RawJSON'][1]
            resp = self._apic_session.push_to_apic(url, data)
            self.resource_id_set(resp.request.body)

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
