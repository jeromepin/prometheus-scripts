#!/usr/bin/env python3

import prometheus_client as prometheus
from prometheus import PrometheusAsyncCollector
from ldap3 import Server, Connection, ALL

def _ldap_connection(host, port=389):
    server = Server(host, port=port, get_info=ALL)
    conn = Connection(server, lazy=True, auto_bind=True)
    return conn

class LDAPCollector(PrometheusAsyncCollector):

    def __init__(self, **kwargs):
        self.conn = _ldap_connection('localhost', 389)

        self.DN_attributes_association = {
            'cn=Total,cn=Connections,cn=Monitor'  : ['monitorCounter'],
            'cn=Bind,cn=Operations,cn=Monitor'    : ['monitorOpInitiated', 'monitorOpCompleted'],
            'cn=Unbind,cn=Operations,cn=Monitor'  : ['monitorOpInitiated', 'monitorOpCompleted'],
            'cn=Search,cn=Operations,cn=Monitor'  : ['monitorOpInitiated', 'monitorOpCompleted'],
            'cn=Compare,cn=Operations,cn=Monitor' : ['monitorOpInitiated', 'monitorOpCompleted'],
            'cn=Modify,cn=Operations,cn=Monitor'  : ['monitorOpInitiated', 'monitorOpCompleted'],
            'cn=Modrdn,cn=Operations,cn=Monitor'  : ['monitorOpInitiated', 'monitorOpCompleted'],
            'cn=Add,cn=Operations,cn=Monitor'     : ['monitorOpInitiated', 'monitorOpCompleted'],
            'cn=Delete,cn=Operations,cn=Monitor'  : ['monitorOpInitiated', 'monitorOpCompleted'],
            'cn=Abandon,cn=Operations,cn=Monitor' : ['monitorOpInitiated', 'monitorOpCompleted'],
            'cn=Extended,cn=Operations,cn=Monitor': ['monitorOpInitiated', 'monitorOpCompleted'],
            'cn=Bytes,cn=Statistics,cn=Monitor'   : ['monitorCounter'],
            'cn=PDU,cn=Statistics,cn=Monitor'     : ['monitorCounter'],
            'cn=Entries,cn=Statistics,cn=Monitor' : ['monitorCounter'],
            'cn=Read,cn=Waiters,cn=Monitor'       : ['monitorCounter'],
            'cn=Write,cn=Waiters,cn=Monitor'      : ['monitorCounter'],
            'cn=Max,cn=Threads,cn=Monitor'        : ['monitoredInfo'],
            'cn=Max Pending,cn=Threads,cn=Monitor': ['monitoredInfo'],
            'cn=Open,cn=Threads,cn=Monitor'       : ['monitoredInfo'],
            'cn=Starting,cn=Threads,cn=Monitor'   : ['monitoredInfo'],
            'cn=Active,cn=Threads,cn=Monitor'     : ['monitoredInfo'],
            'cn=Pending,cn=Threads,cn=Monitor'    : ['monitoredInfo'],
            'cn=Backload,cn=Threads,cn=Monitor'   : ['monitoredInfo'],
            'cn=State,cn=Threads,cn=Monitor'      : ['monitoredInfo']
        }
        self.wanted_DNs = list(self.DN_attributes_association.keys())

        self.setup(**kwargs)

    def _build_metric_name_from_DN(self, DN):
        name = [x.lower() for x in DN.replace('cn=', '').replace(' ', '_').split(',')]
        name.reverse()
        name = 'ldap_' + '_'.join(name)
        return name

    @PrometheusAsyncCollector.run
    def retrieve_monitor_informations(self):
        entries = self.conn.extend.standard.paged_search('cn=Monitor', '(objectClass=*)', attributes=['+', '*'], paged_size=100)
        for entry in entries:
            DN = entry.get('dn')

            if DN in self.wanted_DNs:
                m = prometheus.core.GaugeMetricFamily(self._build_metric_name_from_DN(DN), DN, labels=['type'])

                for attribute in self.DN_attributes_association.get(DN):
                    value = entry.get('attributes').get(attribute)[0]
                    try:
                        value = float(value)
                    except ValueError:
                        value = float(0.0)

                    m.add_metric([attribute], value)

                self.register(m)


if __name__ == '__main__':
    collector = LDAPCollector(port=9200, delay=10)
