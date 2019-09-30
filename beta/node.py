#!/usr/bin/env python
import re
import os
import json
import signal
import socket
import string
import httplib
import argparse
import threading

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

object_store = {}
successors = {}
own_key_space = []
node_addr = ''

class Node(BaseHTTPRequestHandler):

    def send_whole_response(self, code, content, content_type="text/plain"):
        self.send_response(code)
        self.send_header('Content-type', content_type)
        self.send_header('Content-length',len(content))
        self.end_headers()
        self.wfile.write(content)


    def extract_key_from_path(self, path):
        if '/key=' in path:
            return re.split('/key=', path)[1]
        return None


    def do_PUT(self):
        content_length = int(self.headers.getheader('content-length', 0))

        key = self.extract_key_from_path(self.path)

        if key == None:
            self.send_whole_response(400, "No key presented in request")

        if not (all(c in string.hexdigits for c in key)) or len(key) != 32:
            self.send_whole_response(404, "Key: '%s' is not a valid hex string" % key)

        value = self.rfile.read(content_length)
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

    def do_POST(self):
        return self.do_PUT()

    #************************************************************* 

    def forward_query(self, node, key, value):

        res = None
        conn = httplib.HTTPConnection(node, timeout=100)

        if value == None:
            conn.request("GET", '/key='+key)
        else:
            conn.request("PUT", '/key='+key, value)

        resp = conn.getresponse()

        if resp.status == 200:
            res = resp.read().strip()
            conn.close()

        return res

    #****************************************************************************
    def find_best_succ(self, key, value=None):

        key_id = key[-1]

        print 'Searching neighbours: '
        for succ_addr, succ_key_space in successors.items():
            print 'Successor addr: ' + succ_addr
            print 'Successor key space:' + str(succ_key_space)
            if key_id in succ_key_space:
                print 'Neighbour has this key: ' + succ_addr
                print 'Redirecting...'
                print '*********************************************************'
                return self.forward_query(succ_addr, key, value)
            print 'No key'

        min_diff = 16
        max_diff = 0
        min_succ = ''
        max_succ = ''

        print "Key '%s' wasn't found in successors" % key_id
        print 'Searching for the closest successor: '
        for succ_addr, succ_key_space in successors.items():
            print '------------------------------------------------------'
            print 'Successor addr: ' + succ_addr
            print 'Successor key space: ' + str(succ_key_space)

            for kid in succ_key_space:
                t = abs(int(key_id, 16) - int(kid, 16))
                if t < min_diff:
                    min_diff = t
                    min_succ = succ_addr
                if t > max_diff:
                    max_diff = t
                    max_succ= succ_addr

            print 'Min key diff: %d with successor: %s' % (min_diff, min_succ)
            print 'Max key diff: %d with successor: %s' % (max_diff, max_succ)


        if min_diff > 16 - max_diff:
            best_succ = min_succ
        else:
            best_succ = max_succ
        print "Found best successor for redirecting: "
        print "Redirecting to:" + str(best_succ)
        print '************************************************************'
        return self.forward_query(best_succ, key, value)

    #***************************************************************

    def do_GET(self):
        # Check key in general
        if self.path.startswith("/key="):
            key = self.extract_key_from_path(self.path)

            if not (all(c in string.hexdigits for c in key)) or len(key) != 32:
                self.send_whole_response(404, "Key: '%s' is not a valid hex string" % key)

            # Key is correct. Now getting key's id (last character in our case)
            key_id = key[-1]
            
            # ************************************************************************
            print 'Cur key: ' + key_id
            print 'Cur node:' + node_addr
            print 'Cur key_space: ' + str(own_key_space)
            print 'Cur neighbours: ' + str(sorted(successors))
            # ************************************************************************

            # If we responsible for storing this range of keys:
            if key_id in own_key_space:
                if key in object_store:
                    print 'Object is in our store'
                    self.send_whole_response(200, object_store[key])         
                else:
                    print 'Object should be here but it is not yet'
                    self.send_whole_response(404, "No object with key '%s' in the storage" % key)

            # Find the closest successor and forward the query
            else:
                print 'Asking successors'
                answer = self.find_best_succ(key)
                if answer:
                    self.send_whole_response(200, answer)
                else:
                    self.send_whole_response(404, "No object with key '%s' in the storage" % key)


        ##################################################################################################

        # Returns own key space
        elif self.path.startswith("/key_space"):
            self.send_whole_response(200, str(own_key_space))

        # Return all key/value pairs in the node storage
        elif self.path.startswith("/storage"):
            self.send_whole_response(200, str(object_store))

        # Get a list of neighbours (successors)
        elif self.path.startswith("/neighbours") or self.path.startswith("/successors"):
            self.send_whole_response(200, "\n".join(successors) + "\n")

        else:
            self.send_whole_response(404, "Unknown path: " + self.path)


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
    server = HTTPServer((args.host, args.port), Node)
    node_addr = args.host + ':' + str(args.port)

    #-------------------------------------------------------------------------
    f = open("fingers"+str(args.node_num))
    d = json.load(f)

    successors = d['succ']
    own_key_space = d['own']

    f.close()
    os.remove("fingers"+str(args.node_num))

    #--------------------------------------------------------------------------

    def run_server():
        print "Starting node #%d on port %d" % (args.node_num, args.port)
        server.serve_forever()
        print "Node #%d has shut down" % args.node_num

    def shutdown_server_on_signal(signum, frame):
        #print "We get signal (%s). Asking server to shut down" % signum
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
        print "Node # %d reached %.3f second timeout. Asking server to shut down" % (args.node_num, args.die_after_seconds)
        server.shutdown()

    print "Proccess for node #%d exited cleanly" % args.node_num
