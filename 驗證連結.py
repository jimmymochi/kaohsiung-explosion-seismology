# -*- coding: utf-8 -*-
import os, re

base = r"D:\JIMMY CHEN\達意專題\高雄氣爆"
html = open(os.path.join(base, "index.html"), encoding="utf-8").read()
imgs = set(re.findall(r"(\./[^\s\"\'<>]+\.png)", html))
print(f"找到 {len(imgs)} 個圖片引用：")
for i in sorted(imgs):
    p = os.path.normpath(os.path.join(base, i))
    exists = os.path.exists(p)
    print(f"[{'OK' if exists else 'MISSING'}] {i}")
