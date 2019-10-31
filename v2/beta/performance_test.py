#!/usr/bin/env python

import argparse
import httplib
import random
import uuid
import hashlib
import time

def parse_args():
    parser = argparse.ArgumentParser(prog="client", description="DHT client")

    parser.add_argument("nodes", type=str, nargs="+",
                        help="addresses (host:port) of nodes to test")

    return parser.parse_args()

def generate_pairs(count):
    pairs = {}
    for x in range(0, count):
        key = str(uuid.uuid4())
        value = str(uuid.uuid4())
        pairs[key] = value
    return pairs

def put_value(node, key, value):
    conn = httplib.HTTPConnection(node)
    conn.request("PUT", "/storage/"+key, value)
    resp = conn.getresponse()
    if (resp.status != 200) or (resp.status != 204):
        print(resp.read())
    conn.close()
    
def get_value(node, key):
    conn = httplib.HTTPConnection(node)
    conn.request("GET", "/storage/"+key)
    resp = conn.getresponse()
    if resp.status != 200:
        value = None
        print(resp.read())
    else:
        value = resp.read().strip()
    conn.close()
    return value

def get_neighbours(node):
    conn = httplib.HTTPConnection(node)
    conn.request("GET", "/neighbours")
    resp = conn.getresponse()
    if resp.status != 200:
        neighbours = []
    else:
        neighbours = resp.read().strip().split()
    conn.close()
    return neighbours

def walk_neighbours(start_nodes):
    to_visit = start_nodes
    visited = set()
    while to_visit:
        next_node = to_visit.pop()
        visited.add(next_node)
        neighbours = get_neighbours(next_node)
        for neighbor in neighbours:
            if neighbor not in visited:
                to_visit.append(neighbor)
    return visited




def simple_check(nodes):
    print "Simple put/get check, retreiving from same node ..."

    tries = 50
    pairs = generate_pairs(tries)

    successes = 0
    node_index = 0
    for key, value in pairs.iteritems():
        try:
            put_value(nodes[node_index], key, value)
            returned = get_value(nodes[node_index], key)

            if returned == value:
                successes+=1
        except:
            pass
        print('success')

        node_index = (node_index+1) % len(nodes)

    success_percent = float(successes) / float(tries) * 100
    print("Stored and retrieved %d pairs of %d (%.1f%%)" % (
            successes, tries, success_percent ))
    
def retrieve_from_different_nodes(nodes):
    print("Retrieving from different nodes ...")

    tries = 5000
    pairs = generate_pairs(tries)

    successes = 0
    for key, value in pairs.iteritems():
        try:
            put_value(random.choice(nodes), key, value)
            returned = get_value(random.choice(nodes), key)

            if returned == value:
                successes+=1
        except:
            pass
        
    success_percent = float(successes) / float(tries) * 100
    print("Stored and retrieved %d pairs of %d (%.1f%%)" % (
            successes, tries, success_percent ))
    
def get_nonexistent_key(nodes):
    print("Retrieving a nonexistent key ...")

    key = str(uuid.uuid4())
    node = random.choice(nodes)
    print("%s -- GET /%s" % (node, key))
    try:
        conn = httplib.HTTPConnection(node)
        conn.request("GET", "/storage/"+key)
        resp = conn.getresponse()
        value = resp.read().strip()
        conn.close()
        print("Status: %s" % resp.status)
        print("Data  : %s" % value)
    except Exception as e:
        print("GET failed with exception:", e)
        
if __name__ == "__main__":

    args = parse_args()

    nodes = set(args.nodes)
    #nodes |= walk_neighbours(args.nodes)
    nodes = list(nodes)
    print("%d nodes registered: %s" % (len(nodes), ", ".join(nodes)))

    if len(nodes)==0:
        raise RuntimeError("No nodes registered to connect to")

    #print
    #simple_check(nodes)

    #print
    start = time.time()
    retrieve_from_different_nodes(nodes)
    end = time.time()
    print(end)
    print(start)
    print("Throughput in ops/s:")
    print(1/((end -start)/10000))

    #print
    #get_nonexistent_key(nodes)