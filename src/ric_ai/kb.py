import json
import os
from collections import Counter
import math

DEFAULT_KB = [
    {"id": 1, "question": "what is ric ai", "answer": "Ric AI is a simple local AI assistant implemented in Python. It can answer questions from its knowledge base and generate simple replies.", "tags": ["about"]},
    {"id": 2, "question": "how to add knowledge", "answer": "Use the GUI to add or edit knowledge entries, or modify the kb.json file in the application folder.", "tags": ["usage"]},
]


def load_kb(path="kb.json"):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return DEFAULT_KB.copy()


def save_kb(kb, path="kb.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(kb, f, indent=2, ensure_ascii=False)


# Simple cosine similarity over term-frequency vectors
def tokenize(text):
    text = text.lower()
    tokens = [t for t in ''.join(ch if ch.isalnum() else ' ' for ch in text).split() if len(t) > 0]
    return tokens


def tf_counter(text):
    return Counter(tokenize(text))


def cosine_sim(counter1, counter2):
    # compute cosine similarity between two Counters
    intersection = set(counter1.keys()) & set(counter2.keys())
    num = sum(counter1[x] * counter2[x] for x in intersection)
    sum1 = sum(v * v for v in counter1.values())
    sum2 = sum(v * v for v in counter2.values())
    denom = math.sqrt(sum1) * math.sqrt(sum2)
    if denom == 0:
        return 0.0
    return num / denom


def search_kb(kb, query, top_k=3):
    qvec = tf_counter(query)
    scored = []
    for entry in kb:
        text = entry.get("question", "") + " " + entry.get("answer", "")
        sim = cosine_sim(qvec, tf_counter(text))
        scored.append((sim, entry))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]
