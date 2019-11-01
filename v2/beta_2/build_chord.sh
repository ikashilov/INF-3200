#!/bin/bash
# build localhot network from 8 standalone nodes on df port range (starts from 5000)
# args: <1> - every next node is joind to the first one
#		<not specified> - nodes are joind sequentionally


# Replace 'petrunyo' (my localhost) by cluster nodes

if [ [$1 == 1] ]
then
	curl -X POST petrunyo:5000/join?nprime=petrunyo:5001; echo  
	curl -X POST petrunyo:5000/join?nprime=petrunyo:5002; echo
	curl -X POST petrunyo:5000/join?nprime=petrunyo:5003; echo  
	curl -X POST petrunyo:5000/join?nprime=petrunyo:5004; echo
	curl -X POST petrunyo:5000/join?nprime=petrunyo:5005; echo
	curl -X POST petrunyo:5000/join?nprime=petrunyo:5006; echo
	curl -X POST petrunyo:5000/join?nprime=petrunyo:5007; echo
	echo -e

else
	curl -X POST petrunyo:5000/join?nprime=petrunyo:5001; echo  
	curl -X POST petrunyo:5001/join?nprime=petrunyo:5002; echo 
	curl -X POST petrunyo:5002/join?nprime=petrunyo:5003; echo  
	curl -X POST petrunyo:5003/join?nprime=petrunyo:5004; echo
	curl -X POST petrunyo:5004/join?nprime=petrunyo:5005; echo 
	curl -X POST petrunyo:5005/join?nprime=petrunyo:5006; echo  
	curl -X POST petrunyo:5006/join?nprime=petrunyo:5007; echo
fi