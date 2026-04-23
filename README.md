# Aria — AI Voice Companion

A live voice AI companion that listens, understands emotions and responds empathetically.

## What it does
- Listens to your voice automatically
- Detects your emotion
- Replies with empathy using AI
- Speaks back to you
- Runs 100% offline on your laptop

## Requirements
- Python 3.13
- Ollama installed with phi3:mini model

## Setup Instructions

### Step 1 — Install Ollama
Go to ollama.com and install it.
Then run:
ollama pull phi3:mini

### Step 2 — Clone this project
git clone YOUR_REPO_LINK
cd ai-companion

### Step 3 — Create virtual environment
python -m venv venv
venv\Scripts\activate

### Step 4 — Install libraries
pip install -r requirements.txt

### Step 5 — Install ffmpeg
Follow instructions at https://ffmpeg.org

### Step 6 — Run the app
python main.py

## How to use
- Run main.py
- Wait for Aria to greet you
- Start speaking naturally
- Say bye to exit