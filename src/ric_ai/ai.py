from .kb import load_kb, save_kb, search_kb
from .markov import MarkovChain
from .transformer import LocalTransformer
from . import research
import time

class RicAI:
    def __init__(self, kb_path="kb.json"):
        self.kb_path = kb_path
        self.kb = load_kb(self.kb_path)
        self.markov = MarkovChain(order=1)
        self.train_markov()
        # modes: 'offline' (default) or 'online'
        self.mode = 'offline'
        self.transformer = LocalTransformer()

    def set_mode(self, mode: str):
        if mode not in ('offline', 'online'):
            return
        self.mode = mode

    def load_transformer_model(self, model_name: str = 'gpt2', device: str = 'cpu'):
        if not self.transformer.is_available():
            raise RuntimeError('transformers library is not installed')
        self.transformer.load_model(model_name=model_name, device=device)

    def train_markov(self):
        corpus = []
        for e in self.kb:
            corpus.append(e.get("answer", ""))
            corpus.append(e.get("question", ""))
        # Also include some canned phrases
        corpus += [
            "I see, tell me more.",
            "Interesting point.",
            "Can you expand on that?",
        ]
        self.markov = MarkovChain(order=1)
        self.markov.train(corpus)

    def reload_kb(self):
        self.kb = load_kb(self.kb_path)
        self.train_markov()

    def add_kb_entry(self, question, answer):
        nxt = max((e.get("id", 0) for e in self.kb), default=0) + 1
        entry = {"id": nxt, "question": question, "answer": answer}
        self.kb.append(entry)
        save_kb(self.kb, self.kb_path)
        self.train_markov()
        return entry

    def _try_online_answer(self, text: str, creativity: float, use_research: bool = False) -> str:
        # attempt to get an answer from the local transformer if available
        if not self.transformer.is_available():
            return "Online mode requires the optional 'transformers' package installed. See README for setup instructions."
        if not self.transformer.is_loaded():
            try:
                # Try loading a small default model lazily
                self.transformer.load_model('gpt2', device='cpu')
            except Exception as e:
                return f"Failed to load model: {e}"

        # gather KB context
        scored = search_kb(self.kb, text, top_k=3)
        context = []
        if scored:
            for sim, e in scored:
                if sim > 0.05:
                    # include id so the model can "cite" KB entries if used
                    context.append(f"[KB#{e.get('id')}] Q: {e.get('question')} A: {e.get('answer')}")
        context_block = "\n".join(context)

        web_ctx = []
        if use_research:
            # attempt to do a light web search and include snippets
            try:
                results = research.search_duckduckgo(text, max_results=3)
                for i, (title, url, snippet) in enumerate(results, start=1):
                    # try to fetch page text for a more robust snippet
                    page = research.fetch_text_from_url(url, max_chars=1000) if url else ''
                    short = page or snippet or ''
                    if short:
                        web_ctx.append((i, title, url, short[:800]))
            except Exception:
                # research failed; continue without web context
                web_ctx = []

        system_instructions = (
            "You are an expert research assistant. Use the provided context when relevant. "
            "Answer concisely (2-5 sentences). If the context does not contain relevant information, write 'No KB match; answer below' and then answer briefly based on general knowledge. "
            "If you use KB content, prefix sentences with the corresponding [KB#id] tag. If you use web results, prefix sentences with [WEB#n] where n is the result index. Cite URLs when relevant. Do not fabricate sources."
        )

        prompt_parts = [system_instructions]
        if context_block:
            prompt_parts.append("KB Context:\n" + context_block)
        if web_ctx:
            wp = []
            for i, title, url, snippet in web_ctx:
                wp.append(f"[WEB#{i}] {title} ({url})\n{snippet}")
            prompt_parts.append("Web results:\n" + "\n---\n".join(wp))
        prompt_parts.append(f"User question: {text}")
        prompt_parts.append("Assistant (concise answer):")
        prompt = "\n\n".join(prompt_parts)

        # map creativity to temperature (lower creativity => lower temperature)
        temperature = max(0.1, min(1.5, 1.0 - creativity + 0.3))
        try:
            out = self.transformer.generate(prompt, max_new_tokens=300, temperature=temperature)
            if out and len(out.strip()) > 5:
                # prefer answers that aren't just the prompt
                return out.strip()
            return "I couldn't generate a good online answer; try again or switch to offline mode."
        except Exception as e:
            # If transformer fails but we have web_ctx, provide a simple extractive summary
            if web_ctx:
                # simple extraction: return the first sentences that contain query words
                qws = set([w.lower() for w in text.split() if len(w) > 3])
                extracts = []
                for i, title, url, snippet in web_ctx:
                    sents = [s.strip() for s in snippet.split('. ') if s]
                    chosen = []
                    for s in sents:
                        low = s.lower()
                        if any(w in low for w in qws):
                            chosen.append(s)
                            if len(chosen) >= 2:
                                break
                    if not chosen and sents:
                        chosen = sents[:1]
                    if chosen:
                        extracts.append(f"[WEB#{i}] {chosen[0].strip()}")
                if extracts:
                    return "Research summary: " + " -- ".join(extracts)
            return f"Online generation failed: {e}"}

    def respond(self, user_text, creativity=0.8, use_research: bool = False):
        text = user_text.strip()
        if not text:
            return "Could you type something?"
        # simple greetings
        l = text.lower()
        if any(g in l for g in ["hello", "hi", "hey"]):
            return "Hello! I'm Ric. How can I help you today?"
        if any(g in l for g in ["bye", "goodbye", "see you"]):
            return "Goodbye! Feel free to come back with more questions."
        if any(g in l for g in ["thanks", "thank you"]):
            return "You're welcome!"

        # If in online mode, prefer transformer-based research answers
        if self.mode == 'online':
            online = self._try_online_answer(text, creativity, use_research=use_research)
            # if the online answer is substantive, return it
            if online and not online.startswith('Online mode requires') and not online.startswith('Failed to load') and not online.startswith('Online generation failed'):
                return online
        # KB search
        scored = search_kb(self.kb, text, top_k=3)
        if scored:
            top_sim, top_entry = scored[0]
            if top_sim > 0.35:
                return top_entry.get("answer")
            elif top_sim > 0.1:
                # include best two answers
                answers = [e.get("answer") for _, e in scored if _ > 0.1]
                if answers:
                    return "I found some relevant info: " + " -- ".join(answers)

        # fallback: use markov to generate
        # map creativity to temperature
        temp = max(0.0, min(2.0, (1.0 - creativity) * 2.0))
        gen = self.markov.generate(seed=text, max_words=20, temperature=temp)
        # if markov fails, simple reflection
        if gen:
            return gen
        return "I don't know that yet. You can add it to my knowledge base using the Add Knowledge option."