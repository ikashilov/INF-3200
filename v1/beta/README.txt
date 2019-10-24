Run "main_runner.py" form comand line
It can be either run with pyhton 2 or 3

If u wanna test the system by yourself - use POSTMAN app: https://www.getpostman.com/downloads/
You can also run auto test: "simple_test.py" from another terminal window. Or edit it as you wish
Main required test: "req_test.py"
Keys are MD5 hex strings. U can generate ypur own here: https://www.md5hashgenerator.com/
It can  be also uuid (just - sign added)

mai_runner's argument:
    "-n", "--nodes_num", type=int, default=8:         number of nodes to be created
    "-p", "--port_num",  type=int, default=5000,:     initial port for the first node
    "-i", "--nodes_ips", type=str, default=localhost: ip addresses of all nodes in chord


python modules need to be installed:
	* json
	* hashlib
	* httplib
	* argparse
	* threading


The main point of this implementation is that every node know and keeps information about
his successors and knows only thiers keys allocation table, instaed of passing each node the whole table and just recursive go down unti we found the best node to jump