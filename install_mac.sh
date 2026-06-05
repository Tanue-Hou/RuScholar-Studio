#!/bin/bash
set -e

echo "Installing requirements..."
pip install -r requirements.txt

echo "Re-installing llama-cpp-python with Metal support..."
CMAKE_ARGS="-DGGML_METAL=on" pip install --force-reinstall --no-cache-dir llama-cpp-python

echo "Downloading Spacy Russian model (ru_core_news_sm)..."
python -m spacy download ru_core_news_sm

echo "Setup complete!"
