#!/bin/bash

# Define variables
SERVER_REPO="git@github.com:arhodges20/panoptic.git"
SERVER_DIR="/home/ahodges_admin/panoptic"  # Absolute path to the repository directory
SESSION_NAME="panoptic_server"
VENV_DIR="venv"  # Virtual environment will be created inside the server directory

# Function to check and install missing dependencies
install_dependencies() {
    echo "Checking for and installing missing dependencies..."
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y python3 python3-pip tmux git python3-venv
}

# Clone or pull the repository
clone_or_pull_repo() {
    # Check if the panoptic directory exists
    if [ ! -d "$SERVER_DIR" ]; then
        echo "Cloning the Panoptic repository into the panoptic directory..."
        git clone $SERVER_REPO $SERVER_DIR
    else
        echo "Repository already exists in $SERVER_DIR. Pulling the latest changes..."
        cd $SERVER_DIR
        git reset --hard
        git pull origin main
        cd ..
    fi
}

# Function to create and activate the virtual environment
create_and_activate_venv() {
    cd $SERVER_DIR  # Navigate to the server directory
    
    # Check if the virtual environment exists, if not, create it
    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating Python virtual environment..."
        python3 -m venv $VENV_DIR
    else
        echo "Virtual environment already exists."
    fi

    # Activate the virtual environment
    echo "Activating the virtual environment..."
    source $VENV_DIR/bin/activate
}

# Function to install Python dependencies (like Flask)
install_python_dependencies() {
    echo "Installing Python dependencies inside the virtual environment..."
    pip install --upgrade pip
    pip install flask  # Install Flask
}

# Function to start the server in tmux
start_server_in_tmux() {
    echo "Starting the server in a tmux session..."
    
    # Kill any existing session if it exists
    tmux kill-session -t $SESSION_NAME 2>/dev/null  # Ignore error if session doesn't exist
    
    # Start a new tmux session
    tmux new -d -s $SESSION_NAME "cd $SERVER_DIR/server && source $SERVER_DIR/server/venv/bin/activate && python3 server.py; bash" || { 
        echo "Failed to start tmux session"; 
        exit 1; 
    }
    
    echo "Tmux session started successfully"
}

# Main script execution
install_dependencies
clone_or_pull_repo
create_and_activate_venv
install_python_dependencies
start_server_in_tmux

# Final status message
echo "Server setup complete. Use 'tmux attach -t $SESSION_NAME' to monitor the server."
