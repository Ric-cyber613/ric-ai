import os
import pytest
from src.ric_ai import ai as ai_mod

@pytest.mark.skipif(os.environ.get('RUN_WEB_INTEGRATION') != '1', reason='Network integration test disabled')
def test_live_search_and_generate():
    r = ai_mod.RicAI()
    # only run if transformers and web libs are available and local model loaded
    if not (ai_mod.research.AVAILABLE and r.transformer.is_available()):
        pytest.skip('Missing deps for live web integration')
    r.set_mode('online')
    # this performs a real web search and may be slow
    out = r.respond('Tell me about the Eiffel Tower', creativity=0.6, use_research=True)
    assert isinstance(out, str) and len(out) > 0
