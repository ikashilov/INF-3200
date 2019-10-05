import os
import math
import json
import socket
import hashlib
import argparse
import threading

DEF_PORT = 5000
DEF_WORKERS = 8 				# default number of nodes in chain
DEF_IP = socket.gethostname()

# These ain't actual keys. This is key ids for allocation. We use hex strings, so 16
keys = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']

def worker(port, id):
	os.system("./node.py --port " + str(port) + ' -n ' + str(id) )

def create_alloc_table(nodes_ids):
	table = {}
	step = len(keys) // len(nodes_ids)

	j = 0 # C-style programming ;)

	if (len(keys) % len(nodes_ids)) == 0:          
	# case 2,4,8,16
		for i in range(0, len(keys)-step+1, step):
			table[nodes_ids[j]] = keys[i:i+step]
			j+=1
	else:
		bound = len(keys) - len(nodes_ids) * step
		step1 = step + 1
		for i in range(0, bound):
			table[nodes_ids[i]] = keys[j:j+step1]
			j+=step1
		for i in range(bound, len(nodes_ids)):
			table[nodes_ids[i]] = keys[j:j+step]
			j+=step

	return table

def create_dic(node, alloc_table):
	successors = {}
	for succ in fingers[node]:
		successors[succ] = alloc_table[succ]

	d = {'own': alloc_table[node], 'succ': successors} 

	return d
	

def parse_args():
    parser = argparse.ArgumentParser(prog="Vano", description="Distributed storage")
    parser.add_argument("-n", "--nodes_num", type=int, default=DEF_WORKERS, help="number of nodes to be created")
    parser.add_argument("-p", "--port_num", type=int, default=DEF_PORT, help="initial port for the first node")
    parser.add_argument("-i", "--nodes_ips", type=str, default=DEF_IP, help="ip addresses of all nodes in chord", nargs="+")

    return parser.parse_args()

# !######################################################################################################################

args = parse_args()

# Get nodes list 
nodes = []
# We we run at one host but differnt ports:
if args.nodes_ips == DEF_IP:
	all_ports = [str(args.port_num+i) for i in range(args.nodes_num)]
	for port in all_ports:
		nodes.append(DEF_IP+':'+port)
else:
	nodes = args.nodes_ips.split()
# Create nodes ring
nodes_ring = nodes+nodes

alloc_table = create_alloc_table(nodes)
 																		# THIS LOOKS LIKE A MESS  :)
# Magic m-number to create base deduction ring 2
m = int(math.ceil(math.sqrt(args.nodes_num))) 

# Table of each node's successors
fingers = {}
for j, node in enumerate(nodes_ring[:len(nodes)]):
	routes = []
	for i in range(0, m):
		routes.append(nodes_ring[j+2**i])
	fingers[node] = routes

# !######################################################################################################################

thread_list = []
for i, node in enumerate(nodes):

	# We need this to transfer files to another process (I know about interprocess communication, but deadline is tomorrow)
	f = open("fingers"+str(i),'w')
	d = create_dic(node, alloc_table)
	json.dump(d, f)
	f.close()
	# End of super genius crutches

	thread = threading.Thread(target=worker, args=(all_ports[i],i,))
	thread_list.append(thread)
	thread.start()

#print("Whole chord has been successfully started")
