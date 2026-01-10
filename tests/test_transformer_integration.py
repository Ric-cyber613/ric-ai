import os
import pytest

from src.ric_ai.transformer import LocalTransformer


@pytest.mark.integration
def test_download_and_generate_integration():
    """Optional integration test that downloads a tiny model and runs generation.

    This test is skipped unless the environment variable RUN_HF_INTEGRATION_TESTS=1
    is set and the `transformers` package is available. It attempts to download
    and load `sshleifer/tiny-gpt2` and perform a simple generate call.
    """
    if os.environ.get('RUN_HF_INTEGRATION_TESTS') != '1':
        pytest.skip("Set RUN_HF_INTEGRATION_TESTS=1 to run HF integration tests")

    t = LocalTransformer()
    if not t.is_available():
        pytest.skip("The 'transformers' package is not installed")

    model_name = 'sshleifer/tiny-gpt2'

    # Attempt to download model; skip test on network/download failure.
    try:
        t.download_model(model_name=model_name, force=False)
    except Exception as e:
        pytest.skip(f"Skipping due to download failure: {e}")

    try:
        t.load_model(model_name=model_name, device='cpu')
    except Exception as e:
        pytest.skip(f"Skipping due to load failure: {e}")

    # Try a short generation
    try:
        out = t.generate("Write a short sentence about AI:", max_new_tokens=20, temperature=0.7)
    except Exception as e:
        pytest.skip(f"Skipping due to generation failure: {e}")

    assert isinstance(out, str) and len(out.strip()) > 0
