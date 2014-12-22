openstack-heat-apic
====================

Heat plugin for Cisco APIC

# Installation


## Environment

Required

* Python 2.7+
* [acitoolkit](http://datacenter.github.io/acitoolkit/)


## Downloading

Clone the repository

     git clone https://github.com/kecorbin/openstack-heat-plugin

Copy the plugin into heat plugin_dirs (/etc/heat/heat.conf)
    
     cp plugin/apic_plugin.py /usr/lib/heat

Restart openstack-heat-engine

    systemctl restart openstack-heat-engine
    
 