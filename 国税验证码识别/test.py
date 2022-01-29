import os

count = {"0": 0, "1": 0, "2": 0, "3": 0}
symbol_set = set()
files = os.listdir("./captcha")
for file in files:
    content = file.split('_')[0]
    if "\u4e00" <= content[2] <= "\u9fff":
        count["3"] += 1
    elif "\u4e00" <= content[1] <= "\u9fff":
        count["2"] += 1
    elif "\u4e00" <= content[0] <= "\u9fff":
        count["1"] += 1
    else:
        count["0"] += 1
    for i in range(6):
        symbol_set.add(content[i])
print("不含中文的比例：", count["0"] / len(files))
print("含一个中文的比例：", count["1"] / len(files))
print("含两个中文的比例：", count["2"] / len(files))
print("含三个中文的比例：", count["3"] / len(files))
print("所有字符：", sorted(symbol_set))
with open("data/text.txt", 'r', encoding="utf-8") as f:
    captcha_cn = f.read()
for symbol in sorted(symbol_set)[33:]:
    print(captcha_cn.index(symbol), end=" ")