#!/bin/bash

# Define variables
SERVER_REPO="git@github.com:arhodges20/panoptic.git"
SERVER_DIR="panoptic"  # Keep this as 'panoptic', no subdirectory like 'panoptic/agent'
SESSION_NAME="panoptic_agent"
VENV_DIR="venv"
SERVER_URL="http://10.10.50.4:5000/stats"

# Navigate to the correct directory
if [ ! -d "$SERVER_DIR" ]; then
    echo "Cloning the Panoptic repository..."
    git clone $SERVER_REPO
else
    echo "Repository already exists. Pulling the latest changes..."
    cd $SERVER_DIR
    git reset --hard
    git pull origin main
    cd ..
fi

# Create and activate virtual environment
cd $SERVER_DIR/agent
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv $VENV_DIR
else
    echo "Virtual environment already exists."
fi

# Activate the virtual environment
echo "Activating the virtual environment..."
source $VENV_DIR/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install psutil requests

# Deactivate virtual environment after installation
deactivate

# Start the agent using tmux
echo "Starting the agent in a tmux session..."
tmux kill-session -t $SESSION_NAME 2>/dev/null  # Kill any existing session
tmux new -d -s $SESSION_NAME "source $VENV_DIR/bin/activate && python3 agent.py"

# Confirm agent is running
echo "Agent setup complete. Use 'tmux attach -t $SESSION_NAME' to monitor the agent."
