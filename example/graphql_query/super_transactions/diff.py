

all_sets = set([])
f = open("all.csv", "r")
for line in f:
	all_sets.add(line.strip())
f.close()

rsets = set([])
f = open("in2.csv", "r")
for line in f:
	s = line.strip().split('-')[0]
	rsets.add(s)
	if s not in all_sets:
		print("error:", s)
f.close()


for address in list(rsets):
	print(address)
