This is the 'alpha' version of our system.
	* localhost implementation
	* we send non-encrypted key in GET request
	* key and value are any strings (value is a JSON in general)
	* client can push value only to the node he connected to
	* if there is no value on the node client connected to, the node will walk along all his neighbour-nodes to get value for a key,
	  if there is not such value in the network - (404 Not found)
	* POST request is the same as PUT
	* the storage is empty when initialized
	* PUT with a key already presented in storag overwrites the previous data

How to run:
1. Use script main.py from command line
2. Add arguments:
	-n [number of nodes to be created] - default = 2
	-p [port number of the first node (for ports < 1000 u need sudo permission). each next node will increment the port number of previous's node]

How to test:
1. Download Postman
2. Get your localhost name [execute 'hostname' command in bash]
3. Use POSTMAN!
	
	examples:

		Assume we ran at least two nodes on [hostname] on ports 5000 and 5001 respectively


		* PUT value 'Ivan is a cool man' with a key '666' to the node 1 (on port 5001): PUT [hostname]:[5001]/key=666
		And in 'Body' field type: "Ivan is a cool man"

		* GET this value from the same node: GET [hostname]:[5001]/key=666
		* GET this value from another node 2 (on port 5002): GET [hostname]:[5002]/key=666
		We suppose to  get the same value!

		* PUT or GET with broken key (line '/key=' is missing or wrong): GET [hostname]:[5002]/ksadasdaa=666
		We get error 400
		* PUT or GET to nonexistent node: GET [hostname]:[999999]/key=666
		Postman will say that/ Network will continue working

		* Get all nodes in network: GET [hostname]:[5001]/neighbours


Enjoy