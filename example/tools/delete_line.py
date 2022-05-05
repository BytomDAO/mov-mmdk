
def run1():
    arr1 = []
    f = open("ori_btm.txt", "r")
    for line in f:
        line = line.strip()
        if line:
            arr1.append(line)
    f.close()

    arr2 = []
    f = open("to_delete.txt", "r")
    for line in f:
        arr2.append(line.strip())
    f.close()

    out_arr = [x for x in arr1 if x not in arr2]
    f = open("final_btm.txt", "w")
    for line in out_arr:
        f.write(line + "\n")
    f.close()


def run2():
    arr = []
    f = open("ori_btm.txt", "r")
    for line in f:
        line = line.strip()
        if line:
            arr.append(line)
    f.close()

    ori_amount = 0
    has_transfer_amount = 0
    left_amount = 0
    out_arr = []
    bef_set_add = set([])
    arr.reverse()
    for line in arr:
        address, amount = line.split(',')
        ori_amount += float(amount)
        if address not in bef_set_add:
            bef_set_add.add(address)
            has_transfer_amount += float(amount)
        else:
            out_arr.append(line)
            left_amount += float(amount)
    out_arr.reverse()

    check_amount = 0
    arr2 = []
    f = open("to_delete.txt", "r")
    for line in f:
        address, amount = line.strip().split(',')
        check_amount += float(amount)
    f.close()

    f = open("final_btm2.txt", "w")
    for line in out_arr:
        f.write(line + "\n")
    f.close()
    print(f"ori_amount:{ori_amount}, has_transfer_amount:{has_transfer_amount}, "
          f"left_amount:{left_amount}, check_amount:{check_amount}!")

run2()




