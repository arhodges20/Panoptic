#!/bin/bash

# Define variables
SERVER_REPO="git@github.com:arhodges20/panoptic.git"
SERVER_DIR="panoptic/server"
SESSION_NAME="panoptic_server"
PORT=5000
VENV_DIR="venv"

# Update and install necessary packages
echo "Updating system and installing dependencies..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip tmux git python3-venv

# Clone the server repository (if not already cloned)
if [ ! -d "$SERVER_DIR" ]; then
    echo "Cloning the Panoptic repository..."
    git clone $SERVER_REPO
else
    echo "Repository already exists. Pulling the latest changes..."
    cd panoptic
    git reset --hard
    git pull origin main
    cd ..
fi

# Navigate to the server directory
cd $SERVER_DIR

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
pip install flask

# Deactivate the virtual environment
deactivate

# Start the server using tmux
echo "Starting the server in a tmux session..."
tmux kill-session -t $SESSION_NAME 2>/dev/null  # Kill any existing session
tmux new -d -s $SESSION_NAME "source $VENV_DIR/bin/activate && python3 server.py"

# Configure firewall to allow traffic on the specified port
echo "Configuring the firewall to allow traffic on port $PORT..."
sudo ufw allow $PORT

# Confirm the server is running
echo "Server setup complete. Use 'tmux attach -t $SESSION_NAME' to monitor the server."
