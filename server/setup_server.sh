#!/bin/bash

# Define variables
SERVER_REPO="git@github.com:arhodges20/panoptic.git"
SERVER_DIR="panoptic"  # The directory where the repository will be cloned
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
}

# Function to create and activate the virtual environment
create_and_activate_venv() {
    cd $SERVER_DIR  # Navigate to the server directory
    
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

# Function to install Python dependencies
install_python_dependencies() {
    echo "Installing Python dependencies inside the virtual environment..."
    pip install --upgrade pip
    pip install flask
}

# Function to start the server in tmux
start_server_in_tmux() {
    echo "Starting the server in a tmux session..."
    
    # Kill any existing session if it exists
    tmux kill-session -t $SESSION_NAME 2>/dev/null  # Ignore error if session doesn't exist
    
    # Create new tmux session
    tmux new -d -s $SESSION_NAME "source $VENV_DIR/bin/activate && echo 'tmux session created' && python3 server.py" || { 
        echo "Failed to start tmux session"; 
        exit 1; 
    }
    
    echo "Tmux session started successfully"
}

# Function to configure the firewall
configure_firewall() {
    # Check if UFW is installed
    if ! command -v ufw &> /dev/null
    then
        echo "UFW could not be found, installing..."
        sudo apt install ufw -y
    fi

    echo "Configuring the firewall to allow traffic on port 5000..."
    sudo ufw allow 5000
}

# Main script execution
install_dependencies
clone_or_pull_repo
create_and_activate_venv
install_python_dependencies
start_server_in_tmux
configure_firewall

# Final status message
echo "Server setup complete. Use 'tmux attach -t $SESSION_NAME' to monitor the server."
