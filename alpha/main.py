import os
import argparse
import threading

DEF_PORT = 5000
DEF_WORKERS = 2

def worker(port, id, neighbs):
	os.system("./server.py --port " + str(port) + ' -n ' + str(id) + ' --neighbours ' + str(neighbs))

def parse_args():
    parser = argparse.ArgumentParser(prog="Vano", description="Distributed storage")
    parser.add_argument("-n", "--nodes_num", type=int, default=DEF_WORKERS, help="number of nodes to be created")
    parser.add_argument("-p", "--port_num", type=int, default=DEF_PORT, help="initial port for the first node")

    return parser.parse_args()

args = parse_args()

all_ports = [args.port_num+i for i in range(args.nodes_num)]

def get_neighbours(i):
	return [x for x in all_ports if x!=args.port_num+i]

thread_list = []
for i in range(args.nodes_num):
	port = args.port_num + i
	neighbours = get_neighbours(i)

	thread = threading.Thread(target=worker, args=(port,i,neighbours,))
	thread_list.append(thread)
	thread.start()
