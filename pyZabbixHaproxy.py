#!/usr/bin/env python


import csv
import socket
import json
import sys

METRIC_DELIM = '.'  # for the frontend/backend stats
RECV_SIZE = 1024
DEFAULT_SOCKET = '/tmp/haproxy-admin.sock'

class HAProxySocket(object):
    def __init__(self, socket_file=DEFAULT_SOCKET):
        self.socket_file = socket_file

    def connect(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(self.socket_file)
        return s

    def communicate(self, command):
        s = self.connect()
        if not command.endswith('\n'): command += '\n'
        s.send(command)
        result = ''
        buf = ''
        buf = s.recv(RECV_SIZE)
        while buf:
            result += buf
            buf = s.recv(RECV_SIZE)
        s.close()
        return result

    def get_server_info(self):
        result = {}
        output = self.communicate('show info')
        for line in output.splitlines():
            try:
                key, val = line.split(':')
            except ValueError, e:
                continue
            result[key.strip()] = val.strip()
        return result

    def get_server_stats(self):
        output = self.communicate('show stat')
        output = output.lstrip('# ').strip()
        output = [l.strip(',') for l in output.splitlines()]
        csvreader = csv.DictReader(output)
        result = [d.copy() for d in csvreader]
        return json.dumps(result)

def get_stat_item (json_file, psname, item_name):
    filea = open(json_file, mode='r')
    stats = json.load(filea)
    return stats[psname][item_name]

def discovery(DEFAULT_SOCKET, json_file):
    filea = open(json_file, mode='w')
    haproxy = HAProxySocket(DEFAULT_SOCKET)
    try:
        server_stats = json.loads(haproxy.get_server_stats())
    except socket.error, e:
        print e
    data = {'data': []}
    stats = {}
    for statdict in server_stats:
        psname=METRIC_DELIM.join([statdict['pxname'].lower(), statdict['svname'].lower()])
        stats.update({psname: statdict})
        data['data'].append({'{#SRV}': psname})
    filea.write(json.dumps(stats))
    filea.close()
    return json.dumps(data)

def main():
    if len(sys.argv) < 3:
        print discovery(DEFAULT_SOCKET, json_file='/tmp/haproxy_stats.json')
    else:
        print get_stat_item(json_file='/tmp/haproxy_stats.json', psname=sys.argv[1], item_name=sys.argv[2])


if __name__ == "__main__":
    sys.exit(main())
