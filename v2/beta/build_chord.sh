#!/bin/bash
# build network from 4 nodes on
# 	* loaclhost $1 == 1
#	* cluster $1 == 0
# P.S.: $0..$n = args

if [ $1 == 1 ]
then
    curl -X POST petrunyo:5000/join?nprime=petrunyo:5001  
    curl -X POST petrunyo:5000/join?nprime=petrunyo:5002 
    curl -X POST petrunyo:5000/join?nprime=petrunyo:5003  
    curl -X POST petrunyo:5000/join?nprime=petrunyo:5004
else
	curl -X POST compute-0-1:5000/join?nprime=compute-0-2::5000 & 
	curl -X POST compute-0-2:5000/join?nprime=compute-0-3::5000 &
    curl -X POST compute-0-3::5000/join?nprime=compute-0-4::5000 & 
    curl -X POST compute-0-4:5000/join?nprime=compute-0-5:5000
fi

# just an example. U can use python or iterate through node list to avoid copy/past/ Enjoy :)