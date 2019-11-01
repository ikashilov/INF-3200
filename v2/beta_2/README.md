### LOCALHOST TESTING

* Run 'python main_runner.py' for 8 (standard) standalone nodes on localhost (standard) (ports: 5000-5007)  
* Then execute './build_chord.sh' to join all standalone nodes to one chord (also local)  
* Use 'api_check.py' for api check  
* Also 'perfomance_test.py' for PUT/GET throughputs  
* 'multithreading_test.sh' is just the same request to one node (3 times) - in server logs (see output)
request time must be the same for all 3 quiries [very nave]  
* File'bash_command.txt' shows example of the commands on my machine  


### CLUSTER

* Put 'cluster_nodes.txt' (with scraped cluster nodes names) file to the same directory  

* Run the same script, but specify:  
	-t argument as 0 (for running on cluster)  
	-n argumnet with number of standalone nodes to be run (default - 8)  
	-p argument with the first port number of the r first node (all subsequent nodes will increment it, default - 5000)  

* Change 'build_chord.sh' in order to join cluster nodes 
* And also the other commnds ^_^  


 
**And I really encourage you to use POSTMAN for more visualized experiments**