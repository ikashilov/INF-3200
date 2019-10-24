#!/usr/bin/env python
from __future__ import print_function

import re
import os
import ast
import json
import signal
import socket
import string
import httplib
import argparse
import threading

from fingers import *

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn

object_store = {}
successors = {}
own_key_space = []
finger_table = {}

node_host = ''
sim_crash = False
in_chord = False

all_nodes = []
other_nodes = []

successor = ''
predecessor = ''

keys = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']
MAX_KEY_DIFF = len(keys)

class Node(ThreadingMixIn, BaseHTTPRequestHandler):

    def send_whole_response(self, code, content, content_type="text/plain"):
        self.send_response(code)
        self.send_header('Content-type', content_type)
        self.send_header('Content-length', len(content))
        self.end_headers()
        self.wfile.write(content)

    def extract_key_from_path(self, path):
        if '/storage/' in path:
            return re.split('/storage/', path)[1]
        return None

    def do_PUT(self):
        global all_nodes
        global finger_table

        content_length = int(self.headers.getheader('content-length', 0))
        value = self.rfile.read(content_length)

        if sim_crash == True:
            self.send_whole_response(500, "I am sim-crashed")

        if self.path.startswith("/storage/"):
            key = self.extract_key_from_path(self.path)

            if key == None:
                self.send_whole_response(400, "No key presented in request")
                return

            if not (all(c in (string.hexdigits+'-') for c in key)):
                self.send_whole_response(404, "Key: '%s' is not a valid hex string" % key)
                return

            key_id = key[-1]

            # If our node is responsible for storing this values
            if key_id in own_key_space:
                object_store[key] = value
                self.send_whole_response(200, "Value stored for key '%s'" % key)

            else:
                stat = self.find_best_succ(key, value)
                if stat:
                    self.send_whole_response(200, "Value stored for key " + key)
                else:
                    self.send_whole_response(404, "Something wrong")

        # Updating nodes list broadcast
        elif self.path == "/update_node_list":
            all_nodes = ast.literal_eval(value) 
            self.send_whole_response(200, "Nodes list successfully updated")

        # Update finger table broadcast
        elif self.path == "/update_finger_table":
            finger_table = json.loads(value)

            self.update_key_space()
            self.update_successor_predecessor()

            self.send_whole_response(200, "Finger table successfully updated")

        else:
            self.send_whole_response(404, "Unknown path: " + self.path)

    # *************************************************************************************************
    def broadcast_nodes_list(self):
        errs = 0
        value = str(all_nodes)

        for node in other_nodes:
            conn = httplib.HTTPConnection(node)
            conn.request("PUT", "/update_node_list", value)
            resp = conn.getresponse()
            if (resp.status != 200) or (resp.status != 204):
                errs += 1
                print(resp.read())
            conn.close()

        return errs
                                                # Possible to make one 'broadcast' function
    def broadcast_finger_table(self):
        errs = 0
        value = json.dumps(finger_table)

        for node in other_nodes:
            conn = httplib.HTTPConnection(node)
            conn.request("PUT", "/update_finger_table", value)
            resp = conn.getresponse()
            if (resp.status != 200) or (resp.status != 204):
                errs += 1
                print(resp.read())
            conn.close()

        return errs

    def activate_new_node(self, node):
        conn = httplib.HTTPConnection(node)
        conn.request("GET", "/activate")
        resp = conn.getresponse()
        conn.close()

    def update_key_space(self):
        global successors
        global own_key_space

        res = create_dic(node_host, all_nodes, finger_table) 
        successors = res['succ']
        own_key_space = res['own']

    def update_successor_predecessor(self):
        global successor
        global predecessor

        cur_idx = all_nodes.index(node_host)

        if cur_idx == len(all_nodes) - 1:
            successor = all_nodes[0]
        else:
            successor = all_nodes[cur_idx+1]

        if cur_idx == 0:
            predecessor = all_nodes[-1]
        else:
            predecessor = all_nodes[cur_idx-1]

    def exclude_node_from_chord(self):
        global successors, own_key_space, finger_table, \
               in_chord, sim_crash, successor, predecessor

        successors = {}
        own_key_space = []
        finger_table = {}

        sim_crash = False
        in_chord = False

        successor = node_host
        predecessor = node_host

    # ************************************************************************************
    def do_POST(self):

        global sim_crash
        global in_chord
        global all_nodes
        global finger_table

        if self.path == "/sim-recover":
            sim_crash = False
            self.send_whole_response(200, "I got recoverd")

        elif self.path == "/sim-crash":
            sim_crash = True
            self.send_whole_response(200, "")

        elif sim_crash == True:
            self.send_whole_response(500, "I am sim-crashed")

        elif self.path == "/leave":

            # Check if we leaving the which is not in chord
            if in_chord == False:
                self.send_whole_response(406, "Node is not in chord")
                return

            # Remove this node from the nodes lists
            all_nodes.remove(node_host)

            # Update finger table
            finger_table = update_fingers_table(all_nodes)

            # Broadcast nodes list to  all other nodes in the chord
            self.broadcast_nodes_list()

            # Broadcast finger table to other nodes in the chord
            self.broadcast_finger_table()

            # Node is not in chord anymore
            self.exclude_node_from_chord()

            self.send_whole_response(200, "Node '%s' successfully left network" % node_host)


        elif self.path.startswith("/join"):
            nprime = re.sub(r'^/join\?nprime=([\w:-]+)$', r'\1', self.path)

            # Add new node to the nodes lists
            all_nodes.append(nprime)
            # Add new node to the list for broadcasting
            other_nodes.append(nprime)

            # Update finger table
            finger_table = update_fingers_table(all_nodes)

            # Broadcast nodes list to other nodes in the chord
            self.broadcast_nodes_list()

            # Broadcast finger table all to other nodes in the chord
            self.broadcast_finger_table()

            # Update own key space and successors key space
            self.update_key_space()

            # Update successor and predecessor
            self.update_successor_predecessor()

            # crutch
            in_chord = True
            self.activate_new_node(nprime)

            self.send_whole_response(200, "Node '%s' successfully joined network" % nprime)

        else:
            self.send_whole_response(404, "Unknown path: " + self.path)

    #**************************************************************************
    def forward_query(self, node, key, value):

        res = None
        conn = httplib.HTTPConnection(node, timeout=30)

        if value == None:
            conn.request("GET", '/storage/'+key)
        else:
            conn.request("PUT", '/storage/'+key, value)

        resp = conn.getresponse()

        if resp.status == 200:
            res = resp.read().strip()
            conn.close()

        return res

    #**************************************************************************
    def find_best_succ(self, key, value=None):

        key_id = key[-1]

        print('Searching neighbours: ')
        for succ_addr, succ_key_space in successors.items():
            print('Successor addr: ' + succ_addr)
            print('Successor key space:' + str(succ_key_space))
            if key_id in succ_key_space:
                print('Neighbour has this key: ' + succ_addr)
                print('Redirecting...')
                print('*********************************************************')
                return self.forward_query(succ_addr, key, value)
            print('No key')

        min_diff = MAX_KEY_DIFF
        max_diff = 0
        min_succ = ''
        max_succ = ''

        print("Key '%s' wasn't found in successors" % key_id)
        print('Searching for the closest successor: ')
        for succ_addr, succ_key_space in successors.items():
            print('------------------------------------------------------')
            print('Successor addr: ' + succ_addr)
            print('Successor key space: ' + str(succ_key_space))

            for kid in succ_key_space:
                t = abs(int(key_id, 16) - int(kid, 16))
                if t < min_diff:
                    min_diff = t
                    min_succ = succ_addr
                if t > max_diff:
                    max_diff = t
                    max_succ= succ_addr

            print('Min key diff: ', min_diff)
            print('Max key diff: ', max_diff)

        if min_diff <= MAX_KEY_DIFF - max_diff:
            best_succ = min_succ
        else:
            best_succ = max_succ

        #print('Min key diff: %d with successor: %s' % (min_diff, min_succ))
        #print('Max key diff: %d with successor: %s' % (max_diff, max_succ))
        print("Found best successor for redirecting: ", best_succ)
        print("Redirecting to: " + str(best_succ))
        print('************************************************************')
        return self.forward_query(best_succ, key, value)

    # **************************************************************************
    # It's possible to move some request to HEAD sectoin
    def do_GET(self):
        global in_chord

        if sim_crash == True:
            self.send_whole_response(500, "I am sim-crashed")

        if self.path == '/activate':
            in_chord = True
            self.send_whole_response(200, "Node '%s' in now in chord" % node_host)

        if self.path.startswith("/storage/"):

            # First check if we in chord
            if in_chord == False:
                self.send_whole_response(406, "Node is not in the chord")
                return

            # Than check key
            key = self.extract_key_from_path(self.path)
            if key == None:
                self.send_whole_response(400, "No key presented in request")
                return

            if not (all(c in (string.hexdigits+'-') for c in key)): # '-' for uuid support
                self.send_whole_response(404, "Key: '%s' is not a valid hex string" % key)
                return

            # Key is correct. Now getting key's id (last character in our case)
            key_id = key[-1]
            
            # *****************************************************************
            print('Cur key: ' + key_id)
            print('Cur node:' + node_addr)
            print('Cur key_space: ' + str(own_key_space))
            print('Cur neighbours: ' + str(sorted(successors)))
            # *****************************************************************

            # If we responsible for storing this range of keys:
            if key_id in own_key_space:
                if key in object_store:
                    print('Object is in our store')
                    self.send_whole_response(200, object_store[key])         
                else:
                    print('Object should be here, but it is not, yet')
                    self.send_whole_response(404, "No object with key '%s' in the storage" % key)

            # Find the closest successor and forward the query
            else:
                print('Asking successors...')
                answer = self.find_best_succ(key)
                if answer:
                    self.send_whole_response(200, answer)
                else:
                    self.send_whole_response(404, "No object with key '%s' in the storage" % key)

        # ##########################################################################################

        # JSON object with node info
        elif self.path == "/node-info":
            # this 'others' only for stupid api check test
            others = successors.keys()
            if len(others) < 3:
                others = []
            else:
                others.remove(successor)  

            node_info = {
                    "node_key": own_key_space,  # how is this suppose to be either unicode or int while it is list ??
                    "successor": successor,
                    "predecessor": predecessor,
                    "others": others,
                    "sim_crash": sim_crash,
                    "in_chord": in_chord,
                    "route_table": successors
                    }
            node_info_json = json.dumps(node_info, indent=2)
            self.send_whole_response(200, node_info_json, content_type="application/json")

        # If crash simulating activated
        elif sim_crash == True:
            self.send_whole_response(500, "I have sim-crashed")

        # Returns own key space
        elif self.path == "/key_space":
            self.send_whole_response(200, json.dumps(own_key_space), content_type="application/json")

        # Return all key/value pairs in the node storage
        elif self.path.startswith("/stock"):
            self.send_whole_response(200, json.dumps(object_store), content_type="application/json")

        # Get finger global table 
        elif self.path.startswith("/finger_table"):
            self.send_whole_response(200, json.dumps(finger_table), content_type="application/json")

        # Get a list of neighbours (successors)
        elif self.path in ["/neighbours", "/neighbors"]:
            self.send_whole_response(200, "\n".join(successors) + "\n")

        else:
            self.send_whole_response(404, "Unknown path: " + self.path)

# ---------------------------------------------------------------------------------------------------------------------

def parse_args():
    PORT_DEFAULT = 5000
    DIE_AFTER_SECONDS_DEFAULT = 20 * 60
    IP_DEFAULT = socket.gethostname()

    parser = argparse.ArgumentParser(prog="node", description="DHT Node")

    parser.add_argument("-n", "--node_num", type=int, default=0,
                       help="node number")

    parser.add_argument("-ip", "--host", type=str, default=IP_DEFAULT,
                        help="host to start server on by default %s" %IP_DEFAULT)

    parser.add_argument("-p", "--port", type=int, default=PORT_DEFAULT,
                        help="port number to listen on, default %d" % PORT_DEFAULT)

    parser.add_argument("--die-after-seconds", type=float, default=DIE_AFTER_SECONDS_DEFAULT,
                        help="kill server after so many seconds have elapsed, " +
                             "in case we forget or fail to kill it, " +
                             "default %d (%d minutes)" % (DIE_AFTER_SECONDS_DEFAULT, DIE_AFTER_SECONDS_DEFAULT/60))

    return parser.parse_args()


if __name__ == "__main__":

    args = parse_args()

    tmp = args.host.split(':')
    node_addr = tmp[0]
    node_port = int(tmp[1])

    server = HTTPServer((node_addr, node_port), Node)

    node_host = args.host
    all_nodes.append(node_host)
    successor = node_host
    #own_key_space = keys
    #finger_table[args.host] = keys

    def run_server():
        print("Starting node #%d on %s" % (args.node_num, args.host))
        server.serve_forever()
        print("Node #%d has shut down" % args.node_num)

    def shutdown_server_on_signal(signum, frame):
        #print("We get signal (%s). Asking server to shut down" % signum)
        server.shutdown()

    # Start server in a new thread, because server HTTPServer.serve_forever()
    # and HTTPServer.shutdown() must be called from separate threads
    thread = threading.Thread(target=run_server)
    thread.daemon = True
    thread.start()

    # Shut down on kill (SIGTERM) and Ctrl-C (SIGINT)
    signal.signal(signal.SIGTERM, shutdown_server_on_signal)
    signal.signal(signal.SIGINT, shutdown_server_on_signal)

    thread.join(args.die_after_seconds)
    
    if thread.isAlive():
        print("Node # %d reached %.3f second timeout. Asking server to shut down" % (args.node_num, args.die_after_seconds))
        server.shutdown()

    print("Proccess for node #%d exited cleanly" % args.node_num)