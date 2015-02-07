#!/usr/bin/env python
from heat.engine import resource
from heat.openstack.common.gettextutils import _
from heat.openstack.common import log as logging
import acitoolkit.acisession
import acitoolkit.acitoolkit as aci
from oslo.config import cfg

logger = logging.getLogger(__name__)

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

apic_config = cfg.CONF.ml2_cisco_apic
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
        'Rules': {
            'Type': 'List',
            'Default': '',
            'Description': _('List of rules, eg. ["tcp-80","udp-53"]')
        },
        'RawJSON': {
            'Type': 'List',
            'Default': '',
            'Description': _('URL , JSON Data to post')
        },

    }

    attributes_schema = {
        'name': _('Name'),
    }

    def __init__(self, *args, **kwargs):
        """
        Initialize connection to APIC and logs in
        :param args:
        :param kwargs:
        :return:
        """
        super(APIC, self).__init__(*args, **kwargs)

        # ACI Toolkit
        host = cfg.CONF.apic_plugin.apic_host
        username = cfg.CONF.apic_plugin.apic_username
        password = cfg.CONF.apic_plugin.apic_password
        self._apic_session = acitoolkit.acisession.Session('http://' + host, username, password)

        # APIC Mappings
        self.apic_system_id = cfg.CONF.apic_plugin.apic_system_id
        self.app = str(self.apic_system_id) + '_app'
        self.project = str(self.properties['Project'])
        self.tenant = '_' + str(self.apic_system_id) + '_' + str(self.project)

    def _resolve_attribute(self, name):
        if name == 'name':
            return self.physical_resource_name()

    def push_to_apic(self, url, data):
        """
        :param url: URL for POST request
        :param data: body of the POST request
        :return:
        """
        auth = self._apic_session.login()
        logger.info('Authenticated to APIC - Status Code: %s' % auth.status_code)
        resp = self._apic_session.push_to_apic(url, data)
        self.resource_id_set(resp.request.body)
        return resp

    def handle_create(self):
        pass

    def handle_delete(self):
        pass

    def handle_suspend(self):
        pass


class ConsumeContract(APIC):
    """
    A resource which creates a consumer relationship to a contract
    """
    def __init__(self, *args, **kwargs):
        super(ConsumeContract, self).__init__(*args, **kwargs)

    def handle_create(self):
        epg = self.properties['Network']
        contract = self.properties['Contract']
        url = '/api/node/mo/uni/tn-%s/ap-%s/epg-%s.json' \
              % (self.tenant, self.app, epg)
        data = {"fvRsCons": {"attributes": {"tnVzBrCPName": contract, "status": "created"}, "children": []}}
        resp = self.push_to_apic(url, data)
        self.resource_id_set(resp.request.body)


class ProvideContract(APIC):
    """
    A resources which creates a provider relationship to a contract
    """
    def __init__(self, *args, **kwargs):
        super(ProvideContract, self).__init__(*args, **kwargs)

    def handle_create(self):
        epg = self.properties['Network']
        contract = self.properties['Contract']
        url = '/api/node/mo/uni/tn-%s/ap-%s/epg-%s.json' \
              % (self.tenant, self.app, epg)
        data = {"fvRsProv": {"attributes": {"tnVzBrCPName": contract, "status": "created"}, "children": []}}
        resp = self.push_to_apic(url, data)
        self.resource_id_set(resp.request.body)


class CreateContract(APIC):
    """
    A resource which creates a contract
    """
    def __init__(self, *args, **kwargs):
        super(CreateContract, self).__init__(*args, **kwargs)

    def handle_create(self):
        tenant = aci.Tenant(self.tenant)
        contract = aci.Contract(str(self.properties['Contract']), tenant)
        rules = self.properties['Rules']
        logger.info(rules)
        for entry in rules:
            entry = str(entry)
            if entry == 'any':
                aci.FilterEntry(entry, etherT='unspecified', parent=contract)
                break
            protocol_port = entry.split('-')
            aci.FilterEntry(entry,
                            dFromPort=protocol_port[1],
                            dToPort=protocol_port[1],
                            etherT='ip',
                            prot=protocol_port[0],
                            parent=contract)
        url = tenant.get_url()
        data = tenant.get_json()
        logger.info(data)
        self.push_to_apic(url, data)


def resource_mapping():
    return {
        'OS::ACI::APIC': APIC,
        'OS::ACI::ConsumeContract': ConsumeContract,
        'OS::ACI::ProvideContract': ProvideContract,
        'OS::ACI::CreateContract': CreateContract,
    }