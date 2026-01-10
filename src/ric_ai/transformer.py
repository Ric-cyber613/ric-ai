"""LocalTransformer: optional local transformer wrapper.

This module provides a thin wrapper around HuggingFace Transformers for
local generation. It avoids importing heavy libraries until needed and
fails gracefully if `transformers` or `torch` are not installed.

Note: This is optional; the app works in offline mode without it.
"""
from typing import Optional

class LocalTransformer:
    def __init__(self):
        self.available = False
        self.loaded = False
        self.model_name = None
        self.model = None
        self.tokenizer = None
        self.device = 'cpu'
        try:
            import transformers  # noqa: F401
            self.available = True
        except Exception:
            self.available = False

    def is_available(self) -> bool:
        return self.available

    def is_loaded(self) -> bool:
        return self.loaded

    def load_model(self, model_name: str = 'gpt2', device: str = 'cpu') -> None:
        if not self.available:
            raise RuntimeError('transformers library is not installed')
        self.model_name = model_name
        self.device = device
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            # move to device if possible
            if torch.cuda.is_available() and device == 'cuda':
                self.model.to('cuda')
                self.device = 'cuda'
            else:
                self.model.to('cpu')
                self.device = 'cpu'
            self.loaded = True
        except Exception as e:
            self.loaded = False
            raise RuntimeError(f'Failed to load model {model_name}: {e}')

    def generate(self, prompt: str, max_new_tokens: int = 128, temperature: float = 0.8) -> str:
        if not self.loaded or self.model is None or self.tokenizer is None:
            raise RuntimeError('Model not loaded')
        try:
            import torch
            input_ids = self.tokenizer.encode(prompt, return_tensors='pt')
            input_ids = input_ids.to(self.device)
            # sample
            outputs = self.model.generate(
                input_ids,
                do_sample=True,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )
            text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # return only the newly generated part after the prompt if present
            if text.startswith(prompt):
                return text[len(prompt):].strip()
            return text.strip()
        except Exception as e:
            raise RuntimeError(f'Generation failed: {e}')

    def download_model(self, model_name: str = 'gpt2', force: bool = False) -> None:
        """Pre-download model and tokenizer to the local cache.

        This is a convenience wrapper to make it easy to prefetch models offline.
        It will raise a RuntimeError if `transformers` isn't installed or the
        download fails.
        """
        if not self.available:
            raise RuntimeError('transformers library is not installed')
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            # loading both tokenizer and model will download them into cache
            AutoTokenizer.from_pretrained(model_name, force_download=force)
            AutoModelForCausalLM.from_pretrained(model_name, force_download=force)
            return
        except Exception as e:
            raise RuntimeError(f'Failed to download model {model_name}: {e}')
