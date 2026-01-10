#!/usr/bin/env python3
"""CLI to pre-download a transformer model into the local cache."""
import argparse
import sys

from src.ric_ai.transformer import LocalTransformer


def main(argv=None):
    parser = argparse.ArgumentParser(description='Pre-download a transformer model to the local cache')
    parser.add_argument('--model', '-m', default='gpt2', help='Model name (e.g., gpt2)')
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu', help='Preferred device')
    parser.add_argument('--force', action='store_true', help='Force re-download of model files')
    args = parser.parse_args(argv)

    t = LocalTransformer()
    if not t.is_available():
        print("The 'transformers' package is not installed. Install with: pip install transformers torch")
        return 2

    print(f"Downloading model '{args.model}' (force={args.force})...")
    try:
        # Use download_model which fetches tokenizer+model into cache
        t.download_model(model_name=args.model, force=args.force)
        print('Model downloaded to local cache successfully.')
        # Try to do a test load
        t.load_model(model_name=args.model, device=args.device)
        print(f"Model loaded: {t.model_name} on {t.device}")
        return 0
    except Exception as e:
        print('Failed to download/load model:', e)
        return 3


if __name__ == '__main__':
    raise SystemExit(main())