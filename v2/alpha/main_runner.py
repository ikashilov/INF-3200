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

# These are not actual keys. These are key ids for allocation. We use hex strings, so 16
keys16 = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']

def generte_keys():
	hexdigits = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']
	keys = []

	for x in hexdigits:
		for y in hexdigits:
			keys.append(x+y)

	return keys


def worker(host, id):
	os.system("./node.py --host " + host + ' -n ' + str(id) )


def parse_args():
    parser = argparse.ArgumentParser(prog="Chord", description="Distributed storage")
    parser.add_argument("-n", "--nodes_num", type=int, default=DEF_WORKERS, help="number of nodes to be created")
    parser.add_argument("-p", "--port_num", type=int, default=DEF_PORT, help="initial port for the first node")
    parser.add_argument("-i", "--nodes_ips", type=str, default=DEF_IP, help="ip addresses of all nodes in chord", nargs="+")
    parser.add_argument("-t", "--test_state", type=int, default=1, help='if TRUE (1), than run on one host but differnt ports')
    return parser.parse_args()

###############################################################################
# Parse args
args = parse_args()

# Gen keys
if args.test_state == True:
	keys = keys16
else:
	keys = generte_keys()

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

	f.close()
	exit()

###############################################################################
thread_list = []
for i, node in enumerate(nodes):

	#f = open("fingers"+str(i),'w')
	#d = create_dic(node, alloc_table)
	#json.dump(d, f)
	#f.close()

	thread = threading.Thread(target=worker, args=(node,i,))
	thread_list.append(thread)
	thread.start()

print(str(args.nodes_num) + " nodes have been successfully started")