Run "main_runner.py" form comand line

python main_runner.py -n 16 -p 55555

main_runner's arguments:
    "-n", "--nodes_num", type=int, default=8:         number of nodes to be created
    "-p", "--port_num",  type=int, default=5000,:     initial port for the first node
    "-i", "--nodes_ips", type=str, default=localhost: ip addresses of all nodes in chord
