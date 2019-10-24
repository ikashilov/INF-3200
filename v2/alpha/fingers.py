import math

keys = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']

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


def update_fingers_table(nodes):
    # Create nodes ring
    nodes_ring = nodes+nodes

    alloc_table = create_alloc_table(nodes)
                                                
    # Magic m-number to create base deduction ring 2
    m = int(math.ceil(math.sqrt(len(nodes)))) 

    # Table of each node's successors
    fingers = {}
    for j, node in enumerate(nodes_ring[:len(nodes)]):
        routes = []
        for i in range(0, m):
            routes.append(nodes_ring[j+2**i])
        fingers[node] = routes

    return fingers


def create_dic(node, nodes, fingers):
	alloc_table = create_alloc_table(nodes)

	successors = {}
	for succ in fingers[node]:
		successors[succ] = alloc_table[succ]
	d = {'own': alloc_table[node], 'succ': successors} 
	return d