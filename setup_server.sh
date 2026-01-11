#!/bin/bash

# Marzban Bot Setup Script for Linux VPS

echo "--- Starting setup ---"

# Check for Python
if ! command -v python3 &> /dev/null
then
    echo "Python3 could not be found. Please install it (sudo apt install python3 python3-venv)"
    exit
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv and install requirements
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "ATTENTION: Please edit the .env file with your actual credentials!"
fi

echo "--- Setup complete ---"
echo "To activate the environment manually: source venv/bin/activate"
