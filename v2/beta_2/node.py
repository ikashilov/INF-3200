#!/usr/bin/env python
from __future__ import print_function

import re
import os
import ast
import json
import time
import signal
import socket
import string
import httplib
import argparse
import threading

from fingers import *

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn

# Data storage
object_store = {}

# Lookup route: successor: succers key space
successors = {}

# Own key space
own_key_space = []

# Global finger table for all chord
finger_table = {}

# Node addr: 'host:port'
node_host = ''

# Crash simulation state
sim_crash = False

# State of the presence of a node in the chord
in_chord = False

# All nodes in the chord in sequentional order (as been added)
all_nodes = []

successor = ''
predecessor = ''

# Time interval for the chord system self-check
CHECK_TIME = 300


#****************************************************************************************************
#*****************************MAINTENACE FUNCTIONS***************************************************
#****************************************************************************************************


def get_others():
    others = []
    for x in all_nodes:
        if x != node_host:
            others.append(x)
    return others


def system_check():
    global finger_table

    while True:
        time.sleep(CHECK_TIME)
        # if we the only one node in a chord
        if len(all_nodes) < 2:
            continue
        # otherwise we check our successor
        conn = httplib.HTTPConnection(successor)
        conn.request("HEAD","/system-check")
        resp = conn.getresponse()

        if resp.status == 500:

            print("Crashed node found: ", successor)

            all_nodes.remove(successor)

            finger_table = update_fingers_table(all_nodes)

            update_successor_predecessor()
            broadcast_nodes_list()
            broadcast_finger_table()

            print("Crashed node has been excluded from the network")

        conn.close()


def broadcast_nodes_list():
    errs = 0
    value = str(all_nodes)
    other_nodes = get_others()

    for node in other_nodes:
        conn = httplib.HTTPConnection(node)
        conn.request("PUT", "/update_node_list", value)
        resp = conn.getresponse()
        if (resp.status != 200) or (resp.status != 204):
            errs += 1
        conn.close()

    return errs

# Possible to make one 'broadcast' function but this is more demonstrative

def broadcast_finger_table():
    errs = 0
    value = json.dumps(finger_table)
    other_nodes = get_others()

    for node in other_nodes:
        conn = httplib.HTTPConnection(node)
        conn.request("PUT", "/update_finger_table", value)
        resp = conn.getresponse()
        if (resp.status != 200) or (resp.status != 204):
            errs += 1
        conn.close()

    return errs


def broadcast_balance_call():
    other_nodes = get_others()

    for node in other_nodes:
        conn = httplib.HTTPConnection(node)
        conn.request("HEAD", "/balance-system")
        resp = conn.getresponse()
        conn.close()


def activate_new_node(node):
    conn = httplib.HTTPConnection(node)
    conn.request("HEAD", "/activate")
    resp = conn.getresponse()
    conn.close()


def update_key_space():
    global successors
    global own_key_space

    res = create_dic(node_host, all_nodes, finger_table) 
    successors = res['succ']
    own_key_space = res['own']


def update_successor_predecessor():
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


def exclude_node_from_chord():
    global successors, own_key_space, finger_table, storage, \
           in_chord, sim_crash, successor, predecessor, all_nodes

    successors = {}
    own_key_space = []
    finger_table = {}
    storage = {}

    sim_crash = False
    in_chord = False

    successor = node_host
    predecessor = ''

    # This is in case we add node B to node A, than exclude node A
    # from the chord and than add node A to node B (see test case)
    all_nodes = []
    all_nodes.append(node_host)



#****************************************************************************************************
#**************************************NODE CLASS****************************************************
#****************************************************************************************************

class Node(ThreadingMixIn, BaseHTTPRequestHandler):

    # Run continuous systen check
    sys_check_thread = threading.Thread(target=system_check)
    sys_check_thread.daemon = True
    sys_check_thread.start()


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


    def get_key_id(self, key_hash):
        return key_hash[-2:]


    def balance_system(self):
        global object_store
        errs = 0

        # Possible to redirect directly to the node resposible for storing this key/value ? - Nah ))
        node_to_redirect = successor

        for key, value in object_store.items():
            key_id = self.get_key_id(key)
            # if we store data which is not in our key_space anymore
            if not (key_id in own_key_space):
                #print("Found pair to transfer: (%s: %s)" % (key, value))
                # Just send it to succeessor
                # and the value will be automatically stored on proper node
                self.forward_query(node_to_redirect, key, value)
                # Delete it from our storage
                del object_store[key]

        return errs


#****************************************************************************************************
#***************************************PUT**********************************************************
#****************************************************************************************************

    def do_PUT(self):
        global all_nodes
        global finger_table
        global object_store

        content_length = int(self.headers.getheader('content-length', 0))
        value = self.rfile.read(content_length)

        if sim_crash == True:
            self.send_whole_response(500, "I am sim-crashed")

        if self.path.startswith("/storage/"):
            key = self.extract_key_from_path(self.path)

            if key == None:
                self.send_whole_response(400, "No key presented in request")
                return
            '''
            if not (all(c in (string.hexdigits+'-') for c in key)):
                self.send_whole_response(409, "Key: '%s' is not a valid hex string" % key)      EXCLUDED DUE TO API CHECK
                return
            '''
            key_id = self.get_key_id(key)

            # If our node is responsible for storing this values
            if key_id in own_key_space:
                object_store[key] = value
                self.send_whole_response(200, "Value stored for key '%s'" % key)

            else:
                stat = self.find_best_succ(key, value)
                if stat:
                    self.send_whole_response(200, "Value stored for key " + key)
                else:
                    self.send_whole_response(418, "Something wrong")

        # Updating nodes list broadcast
        elif self.path == "/update_node_list":
            all_nodes = ast.literal_eval(value)

            self.send_whole_response(200, "Nodes list successfully updated")

        # Update finger table broadcast
        elif self.path == "/update_finger_table":
            finger_table = json.loads(value)

            update_key_space()
            update_successor_predecessor()

            self.send_whole_response(200, "Finger table successfully updated")

        else:
            self.send_whole_response(404, "Unknown path: " + self.path)

#****************************************************************************************************
#**************************************POST**********************************************************
#****************************************************************************************************
    def do_POST(self):

        global sim_crash
        global in_chord
        global all_nodes
        global finger_table
        global own_key_space

        if self.path == "/sim-recover":
            sim_crash = False
            self.send_whole_response(200, "I've been sim recoverd")

        elif self.path == "/sim-crash":
            sim_crash = True
            self.send_whole_response(200, "I've been sim crashed")

        elif sim_crash == True:
            self.send_whole_response(500, "I am sim-crashed")

        elif self.path == "/leave":
            # Node must be in the chord to be able to leave it
            if in_chord == False:
                self.send_whole_response(200, "Node is not in the chord") # 200 CODE INSTAED OF 406 DUE TO API CHECK
                return

            # Remove this node from the nodes lists
            #if not (node_host in all_nodes):
                # that's impossible
            #else:
            all_nodes.remove(node_host)

            # Update finger table
            finger_table = update_fingers_table(all_nodes)

            # Broadcast nodes list to  all other nodes in the chord
            broadcast_nodes_list()

            # Broadcast finger table to other nodes in the chord
            broadcast_finger_table()

            # Balance this node and broadcast system balace call to the other nodes
            own_key_space = ['empty'] #crutch ^_^
            self.balance_system()
            broadcast_balance_call()

            # Node is not in the chord anymore: delete its all data (i.e. obj storage, fing table succ and pred...)
            exclude_node_from_chord()

            self.send_whole_response(200, "Node '%s' successfully left the network" % node_host)


        elif self.path.startswith("/join"):

            nprime = re.sub(r'^/join\?nprime=([\w:-]+)$', r'\1', self.path)

            # Check if the node is already in the chord
            if nprime in all_nodes:
                self.send_whole_response(405, "Node is already in the chord")
                return

            # Add new node to the nodes lists
            all_nodes.append(nprime)

            # Update finger table
            finger_table = update_fingers_table(all_nodes)

            # Broadcast nodes list to other nodes in the chord
            broadcast_nodes_list()

            # Broadcast finger table all to other nodes in the chord
            broadcast_finger_table()

            # Update own key space and successors key space
            update_key_space()

            # Update successor and predecessor
            update_successor_predecessor()

            # amazing crutch: we are activating the freshly joined node and ourselfs
            in_chord = True
            activate_new_node(nprime)

            # Balance this node and broadcast system balace call to the other nodes
            self.balance_system()
            broadcast_balance_call()

            self.send_whole_response(200, "Node '%s' successfully joined network" % nprime)

        else:
            self.send_whole_response(404, "Unknown path: " + self.path)

    #*************************************************************************************************
    #***********************************LOOKUP FUNCTIONS**********************************************
    #*************************************************************************************************

    def forward_query(self, node, key, value):

        res = None
        conn = httplib.HTTPConnection(node)

        if value == None:
            conn.request("GET", '/storage/'+key)
        else:
            conn.request("PUT", '/storage/'+key, value)

        resp = conn.getresponse()

        if resp.status == 200 or resp.status == 204:
            res = resp.read().strip()
            conn.close()

        return res


    def find_best_succ(self, key, value=None):

        key_id = self.get_key_id(key)

        #print('Searching neighbours: ')
        for succ_addr, succ_key_space in successors.items():
            #print('Successor addr: ' + succ_addr)
            #print('Successor key space:' + str(succ_key_space))
            if key_id in succ_key_space:
                #print('Neighbour has this key: ' + succ_addr)
                #print('Redirecting...')
                #print('*********************************************************')
                return self.forward_query(succ_addr, key, value)
            #print('No key')

        min_diff = MAX_KEY_DIFF
        max_diff = 0
        min_succ = ''
        max_succ = ''

        #print("Key '%s' wasn't found in successors" % key_id)
        #print('Searching for the closest successor: ')
        for succ_addr, succ_key_space in successors.items():
            #print('------------------------------------------------------')
            #print('Successor addr: ' + succ_addr)
            #print('Successor key space: ' + str(succ_key_space))

            for kid in succ_key_space:
                t = abs(int(key_id, 16) - int(kid, 16))
                if t < min_diff:
                    min_diff = t
                    min_succ = succ_addr
                if t > max_diff:
                    max_diff = t
                    max_succ= succ_addr

            #print('Min key diff: ', min_diff)
            #print('Max key diff: ', max_diff)

        if min_diff <= MAX_KEY_DIFF - max_diff:
            best_succ = min_succ
        else:
            best_succ = max_succ

        #print('Min key diff: %d with successor: %s' % (min_diff, min_succ))
        #print('Max key diff: %d with successor: %s' % (max_diff, max_succ))
        #print("Found best successor for redirecting: ", best_succ)
        #print("Redirecting to: " + str(best_succ))
        #print('************************************************************')
        return self.forward_query(best_succ, key, value)


#****************************************************************************************************
#***************************************GET**********************************************************
#****************************************************************************************************

    def do_GET(self):
        global in_chord

        # if we wanna retrive key/value
        if self.path.startswith("/storage/"):

            # First check if we are in chord
            if in_chord == False:
                self.send_whole_response(406, "Node is not in the chord")
                return

            # Then check key
            key = self.extract_key_from_path(self.path)
            if key == None:
                self.send_whole_response(400, "No key presented in request")
                return

            '''
            if not (all(c in (string.hexdigits+'-') for c in key)):
                self.send_whole_response(409, "Key: '%s' is not a valid hex string" % key)      EXCLUDED DUE TO API CHECK
                return
            '''

            # Key is correct. Now getting key's id
            key_id = self.get_key_id(key)
            
            # *****************************************************************
            #print('Cur key: ' + key_id)
            #print('Cur node:' + node_addr)
            #print('Cur key_space: ' + str(own_key_space))
            #print('Cur neighbours: ' + str(sorted(successors)))
            # *****************************************************************

            # If we responsible for storing this range of keys:
            if key_id in own_key_space:
                if key in object_store:
                    #print('Object is in our store')
                    self.send_whole_response(200, object_store[key])         
                else:
                    #print('Object should be here, but it is not, yet')
                    self.send_whole_response(404, "No object with key '%s' in the node's storage" % key)

            # Find the closest successor and forward the query
            else:
                #print('Asking successors...')
                answer = self.find_best_succ(key)
                if answer:
                    self.send_whole_response(200, answer)
                else:
                    self.send_whole_response(404, "No object with key '%s' in the system" % key)

        # *******************************other get requests handlers*****************************

        # JSON object with node info
        elif self.path == "/node-info":
            # this 'others' are only for stupid api check test
            others = successors.keys()
            if len(others) < 3:
                others = []
            else:
                others.remove(successor)  

            node_info = {
                    "node_key": hash(node_host),
                    "successor": successor,
                    "predecessor": predecessor,
                    "others": others,
                    "sim_crash": sim_crash,
                    "in_chord": in_chord,
                    'node key space': ' '.join(map(str, own_key_space))
                    }
            node_info_json = json.dumps(node_info, indent=2)
            self.send_whole_response(200, node_info_json, content_type="application/json")

        # If crash simulating activated
        elif sim_crash == True:
            self.send_whole_response(500, "I am sim-crashed")

        # Returns own key space
        elif self.path == "/key_space":
            self.send_whole_response(200, json.dumps(own_key_space), content_type="application/json")

        # Return all key/value pairs in the node storage
        elif self.path.startswith("/stock"):
            self.send_whole_response(200, json.dumps(object_store), content_type="application/json")

        # Get finger global table 
        elif self.path.startswith("/finger_table"):
            self.send_whole_response(200, json.dumps(sorted(finger_table.items())), content_type="application/json")

        # Get finger global table 
        elif self.path.startswith("/all_nodes"):
            self.send_whole_response(200, " ".join(all_nodes))

        # Get a list of neighbours (successors)
        elif self.path in ["/neighbours", "/neighbors"]:
            self.send_whole_response(200, "\n".join(successors) + "\n")

        else:
            self.send_whole_response(404, "Unknown path: " + self.path)

#****************************************************************************************************
#***************************************HEAD*********************************************************
#****************************************************************************************************

    def do_HEAD(self):
        global in_chord

        if self.path == '/system-check':
            if sim_crash == False:
                self.send_whole_response(200, "OK")
            else:
                self.send_whole_response(500, "CRASHED")

        elif self.path == '/activate':
            in_chord = True
            self.send_whole_response(200, "Node '%s' in now in the chord" % node_host)

        elif self.path == '/balance-system':
            res = self.balance_system()
            if res == 0:
                self.send_whole_response(200, "Node '%s' is successfully balanced" % node_host)
            else:
                self.send_whole_response(218, "Node '%s' is balanced with %d errors" % (node_host, res))


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

    # We assume starting in empty state uncomment to opposite
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