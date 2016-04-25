import logging
import heapq

log = logging.getLogger(__name__)


def journal():
    """Give journal nodes from mine

    :return:
    """
    return __salt__['search.mine_by_host']('roles:hdfs.journalnode')


def nameservices():
    """Give name services from mine

    :return:
    """
    namenodes = _namenodes()
    res = {}
    for host, data in namenodes.items():
        nameservice_name = 'default'
        if 'attributes' in data and 'nameservice' in data['attributes']:
            nameservice_name = data['attributes']['nameservice']
        if nameservice_name not in res:
            res[nameservice_name] = []
        heapq.heappush(res[nameservice_name], (host, data.get('instance_creation_date', 0) ))
    return sorted([{name: _leave_oldest_namenode_hosts(hosts_with_times)} for name, hosts_with_times in res.items()])


def my_nameservice():
    """Returns nameservice if I am part of some or empty name

    :return:
    """
    my_host = __salt__['search.my_host']()
    return _my_nameservice(my_host)


def nameservice_names():
    """Give name services names from mine

    :return:
    """
    name_def = nameservices()
    return sorted([name.keys()[0] for name in name_def])


def is_primary_namenode():
    """True if host was first namenode created

    :return:
    """
    my_host = __salt__['search.my_host']()
    peers = _all_hosts_for_nameservice(my_host)
    return len(peers) > 0 and my_host == peers[0]


def is_secondary_namenode():
    """True if host was second namenode created

    :return:
    """
    my_host = __salt__['search.my_host']()
    peers = _all_hosts_for_nameservice(my_host)
    return len(peers) > 1 and my_host == peers[1]


def my_nameservice_peers():
    """Namenode peers in the same name service

    :return:
    """
    my_host = __salt__['search.my_host']()
    all_peers_including_me = _all_hosts_for_nameservice(my_host)
    return [peer for peer in all_peers_including_me if peer != my_host]


def map_uris(app_name, uris):
    """Map URIs from external URI to HDFS

    :return:
    """
    pkgs_path = __pillar__['hdfs']['pkgs_path']
    ns = nameservice_names()
    return map(lambda x:  'hdfs://{0}{1}/{2}/{3}'.format(ns[0], pkgs_path, app_name, __salt__['system.basename'](x)), uris)


def _leave_oldest_namenode_hosts(hosts_with_times):
    return [x[0] for x in sorted(hosts_with_times, key=lambda x: (x[1], x[0]))[:2]]


def _namenodes():
    search_info = __salt__['search.mine']('roles:hdfs.namenode')
    return {attrs['fqdn']: attrs for attrs in search_info}


def _all_hosts_for_nameservice(my_host):
    name_def = nameservices()
    hosts = [nameservice.values()[0] for nameservice in name_def]
    my_bucket = [host for host in hosts if my_host in host]
    return [y for x in my_bucket for y in x]


def _my_nameservice(my_host):
    name_def = nameservices()
    ns = [name.keys()[0] for name in name_def if my_host in name.values()[0]]
    if len(ns) == 0:
        return ""
    else:
        return ns[0]
