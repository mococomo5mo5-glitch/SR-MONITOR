import json
import os

CURRENT = "calendar.json"
PREVIOUS = "calendar_previous.json"

if not os.path.exists(PREVIOUS):
    os.replace(CURRENT, PREVIOUS)
    print("初回実行")
    exit()

with open(CURRENT, encoding="utf-8") as f:
    current = json.load(f)

with open(PREVIOUS, encoding="utf-8") as f:
    previous = json.load(f)

current_set = {
    (x["date"], x["price"])
    for x in current
}

previous_set = {
    (x["date"], x["price"])
    for x in previous
}

diff = current_set - previous_set

if len(diff) == 0:
    print("変更なし")
else:
    print("変更あり")

    with open("changes.txt", "w", encoding="utf-8") as f:
        for d in sorted(diff):
            f.write(f"{d[0]} : {d[1]}\n")

os.replace(CURRENT, PREVIOUS)
