#!/usr/bin/env python
import argparse
import httplib
import re
import signal
import socket
import threading

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

object_store = {}
neighbours = []

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
            return

        value = self.rfile.read(content_length)
        object_store[key] = value

        self.send_whole_response(200, "Value stored for key " + key)

    def do_POST(self):
        return self.do_PUT()

    #************************************************************* 
    # Here we ask all neighbours either they have value for the key [key]  
    def ask_neighbours(self, key):
        for node in neighbours:

            value = None
            conn = httplib.HTTPConnection(node, timeout=10)
            conn.request("GET", '/ask='+key)
            resp = conn.getresponse()

            if resp.status == 200:
                value = resp.read().strip()
                conn.close()
                break
            conn.close()

        return value

    #***************************************************************

    def do_GET(self):
        # Check key in general
        if self.path.startswith("/key="):
            key = self.extract_key_from_path(self.path)

            if key in object_store:
                self.send_whole_response(200, object_store[key])

            else:
                answer = self.ask_neighbours(key)
                if answer:
                    self.send_whole_response(200, answer)
                else:
                    self.send_whole_response(404, "No object with key '%s' in the storage" % key)

        # If we asking neighbours for a key
        elif self.path.startswith("/ask="):
            key = re.split('/ask=', self.path)[1]

            if key in object_store:
                self.send_whole_response(200, object_store[key])
            else:
                self.send_whole_response(404,"This neighbour doesnt have '%s' key" % key)

        # Get a  list of neighbours
        elif self.path.startswith("/neighbours"):
            self.send_whole_response(200, "\n".join(neighbours) + "\n")

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

    parser.add_argument("--neighbours", type=str, nargs="+",
                        help="ports of neighbour nodes")

    return parser.parse_args()



if __name__ == "__main__":

    args = parse_args()

    server = HTTPServer((args.host, args.port), Node)

    #---------------------------------------------------------------
    # Here we conactenate ip addresses with port numbers for all neighbours
    for n_p in re.findall(r'\d+', str(args.neighbours)):
        neighbours.append(args.host+':'+n_p)
    #---------------------------------------------------------------

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
