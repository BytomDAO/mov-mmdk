
from collections import defaultdict
tj_dic = defaultdict(float)
set_addresses = set([])
tj_set_addresses = set([])
ret = []
f = open("in.csv", "r")
for line in f:
	in_address, out_address, currency, amount, dt = line.strip().split(',')
	if float(amount) > 5000000:
		print(f"{in_address},{out_address},{currency},{amount},{dt}")
		if in_address.startswith("bn"):
			set_addresses.add(in_address)
			tj_dic[in_address] += float(amount)
			if tj_dic[in_address] > 5000000:
				tj_set_addresses.add(in_address)
		if out_address.startswith("bn"):
			set_addresses.add(out_address)
			tj_dic[out_address] += float(amount)
			if tj_dic[out_address] > 5000000:
				tj_set_addresses.add(out_address)
f.close()

print("not right address:", len(set_addresses))
for address in list(set_addresses):
	print(address)

print("tj not right address:", len(tj_set_addresses))
for address in list(tj_set_addresses):
	print(address)
