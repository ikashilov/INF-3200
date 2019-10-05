import os
import argparse
import httplib
import random
import socket
import hashlib
import threading

NODES_NUM_DEFAULT = 7
PORT_DEFAULT = 5000

def simple_test_set():
	res = {}

	k1 = hashlib.md5('Michel').hexdigest()
	v1 = 'Ich bin schwartz'
	k2 = hashlib.md5('Ivan').hexdigest()
	v2 = 'Ya krutoy'
	k3 = hashlib.md5('Sarah').hexdigest()
	v3 = 'Ca va comme ci comme ca'
	k4 = hashlib.md5('Micol').hexdigest()
	v4 = 'Va bene. Cazzo!'

	res[k1] = v1
	res[k2] = v2
	res[k3] = v3
	res[k4] = v4

	return res

def put_value(node, key, value):
    conn = httplib.HTTPConnection(node)
    conn.request("PUT", "/key="+key, value)
    conn.getresponse()
    conn.close()

def get_value(node, key):
    conn = httplib.HTTPConnection(node)
    conn.request("GET", "/key="+key)
    resp = conn.getresponse()
    if resp.status != 200:
        value = None
    else:
        value = resp.read().strip()
    conn.close()
    return value

def worker(num_nodes):
	os.system("./main_runner.py -n " + str(num_nodes))

def parse_args():
    parser = argparse.ArgumentParser(prog="Vano", description="Distributed storage")
    parser.add_argument("-p", "--port_num", type=int, default=PORT_DEFAULT, help="initial port for the first node")
    parser.add_argument("-n", "--nodes_num", type=int, default=NODES_NUM_DEFAULT, help="number of nodes to be created")

    return parser.parse_args()

# --------------------------------------------------------------------------------

if __name__ == "__main__":
	args = parse_args()

	# Preparing stuff
	host = socket.gethostname()
	nodes = []
	ports = [str(args.port_num+i) for i in range(args.nodes_num)]

	for p in ports:
		nodes.append(host+':'+p)

	# We dont need to run in from the thread just do it by ur hands

	#thread = threading.Thread(target=worker, args=(args.nodes_num,)).start()
	
	test_data = simple_test_set()

	for key, value in test_data.items():
		node = random.choice(nodes)
		print('Putting value %s to node: %s' % (value,node))
		put_value(node, key, value)

		node = random.choice(nodes)

		print('Getting value with the key %s from the node: %s' % (key, node))
        got = get_value(node, key)

        print("We got: ", got)

	# You can write whatever you want

