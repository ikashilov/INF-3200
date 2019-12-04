## Version 2
Version 1 extension with the following API:

* GET /node-info List node key, state, and neighbors.  
* POST /join?nprime=<HOST:PORT> Join a network. The node must contact the neighbor node nprime and join nprime’s network.  
* POST /leave Leave the network. The node must go back to its starting singlenode state, and the rest of the network should adjust accordingly. The node may notify its neighbors that it is leaving, or it can be the network’s responsibility to detect the change.  
*  POST /sim-crash Simulate a crash. The node must stop processing requests from other nodes, without notifying them first. Any request or normal  
operational messages between nodes should be either completely refused or
responded to with an error code without being acted upon. The ”crashed”
node must respond correctly only to the /sim-recover and /node-info calls.
The network should detect the crash and respond as if the node has left.
* POST /sim-recover Simulate a crash recovery. The node must ”recover”
from its simulated crashed state and begin responding again to requests
from other nodes. If the network has given up on the node, it should
request to re-join the network via one of its previo  
