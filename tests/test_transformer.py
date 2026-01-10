import pytest
from src.ric_ai import ai as ai_mod
from src.ric_ai.transformer import LocalTransformer


def test_transformer_availability():
    t = LocalTransformer()
    # Should return a boolean and not raise
    assert isinstance(t.is_available(), bool)


def test_mock_generation(monkeypatch):
    class MockTrans:
        def __init__(self):
            self._loaded = True
            self.model_name = 'mock'
            self.device = 'cpu'

        def is_available(self):
            return True

        def is_loaded(self):
            return True

        def load_model(self, model_name, device='cpu'):
            self.model_name = model_name
            self.device = device
            self._loaded = True

        def generate(self, prompt, max_new_tokens=128, temperature=0.8):
            return 'MOCK ANSWER: This is a mock response.'

    # Patch the LocalTransformer used inside ai module
    monkeypatch.setattr(ai_mod, 'LocalTransformer', MockTrans)

    ric = ai_mod.RicAI()
    ric.set_mode('online')
    ans = ric.respond('Tell me something interesting', creativity=0.5)
    assert 'MOCK ANSWER' in ans
*** End Patch