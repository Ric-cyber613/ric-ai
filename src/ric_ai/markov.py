import random
from collections import defaultdict

class MarkovChain:
    def __init__(self, order=1):
        self.order = order
        self.chain = defaultdict(list)

    def train(self, texts):
        for text in texts:
            words = self._tokenize(text)
            if len(words) <= self.order:
                continue
            for i in range(len(words) - self.order):
                key = tuple(words[i:i + self.order])
                next_word = words[i + self.order]
                self.chain[key].append(next_word)

    def generate(self, seed=None, max_words=30, temperature=1.0):
        if not self.chain:
            return ""
        if seed:
            seed_words = self._tokenize(seed)
            # try to find a key that matches the last words
            for k in range(len(seed_words)):
                key = tuple(seed_words[-(k+1):])
                if len(key) == self.order and key in self.chain:
                    current = list(key)
                    break
            else:
                current = list(random.choice(list(self.chain.keys())))
        else:
            current = list(random.choice(list(self.chain.keys())))

        out = list(current)
        for _ in range(max_words - self.order):
            key = tuple(out[-self.order:])
            options = self.chain.get(key)
            if not options:
                break
            # temperature controls randomness: higher => more random
            if temperature <= 0.0:
                choice = max(set(options), key=options.count)
            else:
                # sample with simple weighted randomness
                if random.random() < (1.0 / (1.0 + temperature)):
                    # pick most common
                    choice = max(set(options), key=options.count)
                else:
                    choice = random.choice(options)
            out.append(choice)
        return self._detokenize(out)

    def _tokenize(self, text):
        return [w for w in ''.join(ch if ch.isalnum() or ch.isspace() else ' ' for ch in text.lower()).split() if w]

    def _detokenize(self, words):
        if not words:
            return ""
        s = " ".join(words)
        return s.capitalize() + ("." if not s.endswith((".", "?", "!")) else "")
