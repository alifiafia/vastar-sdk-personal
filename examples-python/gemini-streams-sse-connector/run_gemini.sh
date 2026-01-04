#!/bin/bash

echo "🌐 Running with REAL Gemini API..."

# Non-aktifkan simulator
export USE_SIMULATOR=false

# Pastikan API key sudah ada
if [ -z "$GEMINI_API_KEY" ]; then
  echo "❌ GEMINI_API_KEY not set!"
  echo "Set it first with: export GEMINI_API_KEY=YOUR_KEY"
  exit 1
fi

python3 main.py
