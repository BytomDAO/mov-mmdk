
forbid_contract_address = [
	"0xE30A8729c40a982d8Fc236eA1d3CFfFa98494056", 
	"0xa6FC11CffE4254e3d71B524d489bB1B9211e7413", 
	"0xBD92EBe7A7b2Edbf4c7dc4B0225677297275b986", 
	"0x5F5EC64BC0eE0bc46eD0AF5c44B15deA6274d726",
	"0x9e0738620F6511901DD909e3A13A24A7aF534A1e",

	# human add
	"0xF5cd39Cc2A42CD19c80EBd60BF5e2446A3Dc1548",
	"0xcC6a8FC6056b28AdD425F09cae6C31445d03e1Bf",
	"0x457819c49415447517BAf00D37c8B2708A4dB756",
	"0xBaB08A3bE9Dc0416483cC254b272841D4680580f",
	"0xf0FEFd6015181ED236c367Eb77a7971cFEcaAc1a",
	"0x8F6f9202a86341C3Ff2f00Cf0dE1b998d440C608",
	"0x085F3A40c7841a813e4a8323885f8949f063723d",
	"0xC9B36b3Dd8F95EA802f1d438b7693044C869a6Df",
	"0x265353aFae702617056f9073FFa9507369adc06F",
	"0xC171EBfF9ad38f0af764ae73418B951b7B6DD9a1",


	"0xC57b92cc78A32f554948A495337Ed34c5967772F",
	"0xEE95d6490321C69327500Cc4755742aFf947E693",
	"0x3A5906A1Ba92c52A81a4398C161085d637A1caB0",
	"0xc8B48BccdF1256b6ac6F9Ef4447146353F1F9005",
	"0xf7486a77393eD573B1a9991B7877EDBeaA0af86b",
	"0xcadB9D267BCd0040231d0bA56926B44F233b11D6",
	"0x1a25A977AE221757Cf4e84Fc496147565d374863",
	"0x8ACb2342781b01AcD261a02c7b0616dd987CFee0"
]

#sadd = set([])
sadd = set(forbid_contract_address)
f = open("in.csv", "r")
for line in f:
	arr = line.strip().split(',')
	add1 = arr[0]
	add2 = arr[1]
	if add1.startswith('0x'):
		sadd.add(add1)
	if add2.startswith('0x'):
		sadd.add(add2)
f.close()


all_lines = []
w1 = set([])
f = open("bmc_btm_transfer.csv", "r")

flag = True
for line in f:
	if flag:
		flag = False
		continue
	arr = line.strip().split(',')
	amount = float(arr[10]) * 1.0 / (10 ** 18)
	from_address = arr[-2].replace('"', "")
	to_address = arr[-1].replace('"', "")

	# print(amount, from_address, to_address)

	if from_address not in sadd and to_address not in sadd:
		all_lines.append([from_address, to_address, amount, "btm"])
		# print(from_address, to_address, amount)
		w1.add(from_address)
		w1.add(to_address)

f.close()

print("??")
flag = True
f = open("bmc_tokens_transfer.csv", "r")
for line in f:
	if flag:
		flag = False
		continue

	arr = line.strip().split(',')
	from_address = arr[-3].replace('"', "")
	to_address = arr[-2].replace('"', "")
	asset = arr[-1].replace('"', "")
	if from_address not in sadd and to_address not in sadd:
		all_lines.append([from_address, to_address, amount, asset])
		# print(from_address, to_address, amount)
		w1.add(from_address)
		w1.add(to_address)


f.close()

# print("\n\n")
# for k_address in w1:
# 	print(k_address)

# print(all_lines)

while True:
	update = False
	for from_address, to_address, amount, asset in all_lines:
		if from_address in sadd or to_address in sadd:
			update = True
			sadd.add(from_address)
			sadd.add(to_address)
	if not update:
		break

for address in forbid_contract_address:
	sadd.add(address)

print("result")
result_address_sets = set([])
result_arr = []
for from_address, to_address, amount, asset in all_lines:
	if from_address not in sadd and to_address not in sadd:
		print(from_address, to_address, amount)
		result_arr.append([from_address, to_address, amount])
		result_address_sets.add(from_address)
		result_address_sets.add(to_address)

for address in result_address_sets:
	print(address)
print("result_arr:", len(result_arr))
print("len:result_address_sets", len(result_address_sets))

