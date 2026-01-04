#!/bin/bash

echo "🚀 Starting Gemini Connector with RAI Simulator..."

# Aktifkan simulator
export USE_SIMULATOR=true
export GEMINI_API_KEY=DUMMY

# Jalankan program utama
python3 main.py

echo "🛑 Connector stopped."
