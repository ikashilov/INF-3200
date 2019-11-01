#!/bin/bash
# Multithreading test
# Send any request multiple times an look at time on server

curl petrunyo:5000/key_space & curl petrunyo:5000/key_space & curl petrunyo:5000/key_space