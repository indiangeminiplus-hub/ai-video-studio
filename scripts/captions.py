"""Karaoke caption chunks (3–6 words, avg ~4.3) from words.json.

usage: python captions.py <words.json> <out_captions.json> [--fix "chơi biết=chưa biết;rưu rương=du dương"]
Output: [{"t0", "t1", "words": [{"w","s","e"}]}]
--fix replaces word sequences (whisper mistakes) before chunking; keeps the original timings.
"""
import argparse
import json

ap = argparse.ArgumentParser()
ap.add_argument("words")
ap.add_argument("out")
ap.add_argument("--fix", default="")
ap.add_argument("--max", type=int, default=5)
ap.add_argument("--min", type=int, default=3)
ap.add_argument("--max-dur", type=float, default=1.6)
a = ap.parse_args()

words = json.load(open(a.words))

for pair in filter(None, a.fix.split(";")):
    src, dst = (x.strip().split() for x in pair.split("="))
    i = 0
    while i <= len(words) - len(src):
        if [w["w"].lower().strip(",.?!") for w in words[i:i + len(src)]] == [x.lower() for x in src]:
            s, e = words[i]["s"], words[i + len(src) - 1]["e"]
            step = (e - s) / len(dst)
            words[i:i + len(src)] = [{"w": d, "s": round(s + k * step, 3), "e": round(s + (k + 1) * step, 3)} for k, d in enumerate(dst)]
            i += len(dst)
        else:
            i += 1

chunks, cur = [], []
# Glue "%", "-4" etc. onto the previous token so "100%" / "3-4" stay one word.
glued = []
for w in words:
    if glued and w["w"][:1] in "%-–":
        glued[-1] = {"w": glued[-1]["w"] + w["w"], "s": glued[-1]["s"], "e": w["e"]}
    else:
        glued.append(dict(w))
words = glued

# Vietnamese clause openers: a new chunk prefers to start here.
OPENERS = {"để", "nhưng", "tuy", "và", "hay", "thì", "khi", "cho", "với", "nếu", "thay", "bây", "tại", "ngày", "ngay", "mà"}
for w in words:
    tok = w["w"].lower()
    sentence_start = w["w"][:1].isupper() and w["w"] not in ("AI",)
    if cur and ((sentence_start and len(cur) >= 2) or (tok in OPENERS and len(cur) >= a.min)):
        chunks.append(cur)
        cur = []
    cur.append(w)
    punct = w["w"][-1:] in ",.?!"
    dur = cur[-1]["e"] - cur[0]["s"]
    if len(cur) >= a.max or (punct and len(cur) >= a.min) or (dur >= a.max_dur and len(cur) >= a.min):
        chunks.append(cur)
        cur = []
if cur:
    if chunks and len(cur) < a.min:
        chunks[-1] += cur
    else:
        chunks.append(cur)

out = []
for i, c in enumerate(chunks):
    t1 = chunks[i + 1][0]["s"] if i + 1 < len(chunks) else c[-1]["e"] + 0.3
    out.append({"t0": round(c[0]["s"], 3), "t1": round(t1, 3),
                "words": [{"w": w["w"].strip(",.!"), "s": w["s"], "e": w["e"]} for w in c]})
json.dump(out, open(a.out, "w"), ensure_ascii=False, indent=1)
print(f"{len(out)} chunks, avg {sum(len(c['words']) for c in out) / max(1, len(out)):.1f} words")
