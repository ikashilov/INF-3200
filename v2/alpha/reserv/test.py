import re
import pandas as pd

def generte_keys():
	hexdigits = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']
	keys = []

	for x in hexdigits:
		for y in hexdigits:
			keys.append(x+y)

	return keys

df =  pd.read_csv("cluster_nodes.txt", sep=" ")
#print df.iloc[:,0].tolist()
f = open('tmp.txt','w')
f.write(str(df.iloc[:,0].tolist()))
f.close()

f = open('tmp.txt','r')

nodes = re.sub(r'[^a-z0-9- ]', "",f.read()).split()

f.close()

for n in nodes:
	print n
