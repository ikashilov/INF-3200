import os
import re
import math
import json
import socket
import hashlib
import argparse
import threading

DEF_PORT = 5000                 # default number of port
DEF_WORKERS = 8 				# default number of nodes in chain
DEF_IP = socket.gethostname()
CLUSTER_NODES_INFO_FILE = "cluster_nodes.txt"


def worker(host, id):
	os.system("./node.py --host " + host + ' -n ' + str(id) )


def parse_args():
    parser = argparse.ArgumentParser(prog="Chord", description="Distributed storage")
    parser.add_argument("-n", "--nodes_num", type=int, default=DEF_WORKERS, help="number of nodes to be created")
    parser.add_argument("-p", "--port_num", type=int, default=DEF_PORT, help="initial port for the first node")
    parser.add_argument("-i", "--nodes_ips", type=str, default=DEF_IP, help="ip addresses of all nodes in chord", nargs="+")
    parser.add_argument("-t", "--test_state", type=int, default=1, help='if TRUE (1), than run on one host but differnt ports')
    return parser.parse_args()

# *******************************************************************************************************

args = parse_args()

# Get nodes list
nodes = []
if args.test_state == True:
	all_ports = [str(args.port_num+i) for i in range(args.nodes_num)]
	for port in all_ports:
		nodes.append(DEF_IP+':'+port)

else:
	f = open(CLUSTER_NODES_INFO_FILE,'r')
	all_cluster_nodes = re.sub(r'[^a-z0-9- ]', "",f.read()).split()
	all_cluster_nodes[:args.nodes_num]

	for cl_node in all_cluster_nodes[:args.nodes_num]:
		nodes.append(cl_node + ':' + str(DEF_PORT))

# Run all nodes in a separate thread (nodes are in the single state)
thread_list = []
for i, node in enumerate(nodes):
	thread = threading.Thread(target=worker, args=(node,i,))
	thread_list.append(thread)
	thread.start()

print(str(args.nodes_num) + " nodes have been successfully started")