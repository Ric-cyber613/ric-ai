import pytest
from src.ric_ai import ai as ai_mod


class MockResearch:
    def search_duckduckgo(self, q, max_results=3):
        return [('Title1','http://example.com/1','Snippet1'), ('Title2','http://example.com/2','Snippet2')]
    def fetch_text_from_url(self, url, max_chars=1000):
        return 'This is a sample page text mentioning quantum and physics.'

class MockTrans:
    def is_available(self):
        return True
    def is_loaded(self):
        return True
    def load_model(self, model_name, device='cpu'):
        pass
    def generate(self, prompt, max_new_tokens=200, temperature=0.7):
        # ensure web context included
        assert 'Web results:' in prompt or '[WEB#1]' in prompt
        return 'MOCKED ANSWER referencing [WEB#1]'


def test_online_research(monkeypatch):
    monkeypatch.setattr(ai_mod, 'research', MockResearch())
    monkeypatch.setattr(ai_mod, 'LocalTransformer', MockTrans)
    r = ai_mod.RicAI()
    r.set_mode('online')
    out = r.respond('Tell me about quantum entanglement', creativity=0.5, use_research=True)
    assert 'MOCKED ANSWER' in out
