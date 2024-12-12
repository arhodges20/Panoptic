#!/bin/bash

# Define variables
AGENT_REPO="git@github.com:arhodges20/panoptic.git"
AGENT_DIR="panoptic/agent"
SERVER_URL="http://10.10.50.4:5000/stats"

# Update and install necessary packages
echo "Updating system and installing dependencies..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip tmux git

# Clone the agent repository (if not already cloned)
if [ ! -d "$AGENT_DIR" ]; then
    echo "Cloning the Panoptic repository..."
    git clone $AGENT_REPO
else
    echo "Repository already cloned. Pulling latest changes..."
    cd panoptic && git pull && cd ..
fi

# Navigate to the agent directory
cd $AGENT_DIR

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install psutil requests

# Configure the server URL in the agent script (optional)
echo "Configuring the server URL..."
sed -i "s|SERVER_URL = .*|SERVER_URL = \"$SERVER_URL\"|" agent.py

# Start the agent using tmux
SESSION_NAME="panoptic_agent"
echo "Starting the agent in a tmux session..."
tmux kill-session -t $SESSION_NAME 2>/dev/null  # Kill any existing session
tmux new -d -s $SESSION_NAME "python3 agent.py"

# Confirm the agent is running
echo "Agent setup complete. Use 'tmux attach -t $SESSION_NAME' to monitor the agent."
