This is the simpliest version of distributed data storage v2 (with join/leave api and crash simulating)
Simpliest means it does not transfer data after join/leave. But it satisfyes assignmemt requirements

How to run

use 'python main_runner.py' command to run n nodes each in a single state:
	* -n arg: number of nodes to be created
	* -t arg: test state - if True (1),than  create and run nodes on local host but differt ports 
							(-p arg specifies port to satrt incremnting for all n nodes (default - 5000)); 
						 - if False (0), than create and run nodes on cluster (takes the first n nodes from 'cluster_nodes.txt file')


each node starts in a separate thread, so dont forget to make 'node.py' file executable 
by following command: "chmod +x node.py"

each nodes accepts multithreadng i.e. multiple requets in the same time. 
	To check it run "multithreading_test.sh" (also need to be executable)
	It send any (key_space or whatever u like) request to one node three times.
	Make sure it is multithreading by looking at server logs (output) or script (curl) output:
	Time has to be the same for all three requests

To connect nodes to a network use join API:
	* from command line (curl):
	  curl -X POST 'http://node1_host:node1_port/join?nprime=node2_host:node2_port
	* from POSTMAN app:
		selcet POST request type and write: 'http://node1_host:node1_port/join?nprime=node2_host:node2_port
	*  from python script using httplib

I wrote a simple "build_chord.sh" bash script (dont forget to make it executable),
as an example of the first option
	* arg1 = 1 to specify tetsing on localhost
	  arg1 = 0 for cluster

	  nodes can be joind sequentionally i.e. node1+node2 & node2+node3 & node3+node4 
	  or not: node1+node2 & node1+node3 & node1+node4. 
	  In second case system will force to join node after the last one in a chord (i.e. to the option 1)
	  IMPORTANT! join api can't be executed in parrallel (need some locker mechamnism to create right finger table)

Then run 'api_check.py' script to check api. Specify any of two nodes from the chord
IMPORTANT! nodes must be joined to a network. Not just run in a single state

file 'cluster_nodes.txt' was scrapedd from uv cluster by executing the following command:
	"rocks list host" on cluster. Everything else were filtered so only nodes names are left
