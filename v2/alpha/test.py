import re
import pandas as pd
import uuid
import string
import json

def generte_keys():
	hexdigits = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']
	keys = []

	for x in hexdigits:
		for y in hexdigits:
			keys.append(x+y)

	return keys

#df =  pd.read_csv("cluster_nodes.txt", sep=" ")
#print df.iloc[:,0].tolist()
#f = open('tmp.txt','w')
#f.write(str(df.iloc[:,0].tolist()))
#f.close()

#f = open('tmp.txt','r')

#nodes = re.sub(r'[^a-z0-9- ]', "",f.read()).split()
'''
#f.close()
a = '01'
b = '11'
#print int(a, 16) - int(b, 16)

d = {'key': 666}
s = json.dumps(d)
print s, type(s)

f = json.loads(s)
print type(f), f
'''

a = [1,2,3,4,5,6]
print len(a)

print json.dumps(a)