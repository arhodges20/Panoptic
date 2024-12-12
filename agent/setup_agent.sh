#!/bin/bash

# Define variables
SERVER_REPO="git@github.com:arhodges20/panoptic.git"
SERVER_DIR="../panoptic"  # Use relative path to the parent panoptic directory
SESSION_NAME="panoptic_agent"
VENV_DIR="venv"  # Virtual environment will be created inside the agent folder
SERVER_URL="http://10.10.50.4:5000/stats"

# Update and install necessary packages
echo "Updating system and installing dependencies..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip tmux git python3-venv

# Navigate to the parent directory and clone the repository if it doesn't exist
if [ ! -d "$SERVER_DIR" ]; then
    echo "Cloning the Panoptic repository..."
    git clone $SERVER_REPO $SERVER_DIR
else
    echo "Repository already exists. Pulling the latest changes..."
    cd $SERVER_DIR
    git reset --hard
    git pull origin main
    cd ..
fi

# Navigate to the agent directory
cd $SERVER_DIR/agent

# Create a virtual environment if it doesn't already exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv $VENV_DIR
else
    echo "Virtual environment already exists."
fi

# Activate the virtual environment
echo "Activating the virtual environment..."
source $VENV_DIR/bin/activate

# Install Python dependencies inside the virtual environment
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install psutil requests

# Deactivate the virtual environment after installation
deactivate

# Start the agent using tmux
echo "Starting the agent in a tmux session..."
tmux kill-session -t $SESSION_NAME 2>/dev/null  # Kill any existing session
tmux new -d -s $SESSION_NAME "source $VENV_DIR/bin/activate && python3 agent.py"

# Confirm the agent is running
echo "Agent setup complete. Use 'tmux attach -t $SESSION_NAME' to monitor the agent."
