# Panoptic

A real-time system monitoring solution with a web dashboard that tracks system statistics and process information. Features secure authentication through Keycloak.

## Overview

This project consists of three main components:

1. **Monitoring Agent (Python)**
   - Collects system metrics (CPU, memory usage)
   - Tracks new process creation
   - Detects privileged process execution
   - Sends data to central server

2. **Backend Server (Flask/Python)**
   - Receives and stores monitoring data
   - Provides API endpoints for data access
   - Integrates with Keycloak for authentication
   - Uses SQLite for data storage

3. **Web Dashboard**
   - Displays real-time system metrics
   - Shows process information in sortable grids
   - Visualizes data with interactive charts
   - Allows filtering by date/time ranges

## Features

- **System Monitoring**
  - Real-time CPU and memory usage tracking
  - New process detection
  - Privileged process alerts
  - Historical data storage

- **Data Visualization**
  - Interactive charts for system metrics
  - Sortable and filterable data grids
  - Custom date range selection
  - Real-time updates

- **Security**
  - Keycloak authentication
  - Secure API endpoints
  - Session management
