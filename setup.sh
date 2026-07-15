#!/bin/bash
# setup.sh — Boxes environment bootstrap and update helper.
#
# Usage:
#   ./setup.sh prod [venv_dir]   # install, migrate, loaddata, processjs
#   ./setup.sh dev  [venv_dir]   # prod + seed demo data via Celery
#   ./setup.sh update [venv_dir] # pip install -r requirements.txt, migrate, processjs
#   ./setup.sh check [venv_dir]  # manage.py check --deploy
#
# Second argument overrides the virtualenv directory (default: env).
# Requires virtualenv on PATH and a readable /etc/boxes.env for Django commands.
#
# See docs/SETUP.md and docs/DEVELOPMENT.md.


# Allow for custom venv names while defaulting to env if none is provided
if [ "$2" != "" ]
then
    VENV_DIR="$2"
else
    VENV_DIR="env"
fi

PYTHON_PATH="$VENV_DIR/bin/python3"

function setup_virtualenv() {
    # Create venv if missing and install requirements.txt
    if [ ! -d "$VENV_DIR" ]; then
        echo "Setting up the virtual environment..."
        virtualenv $VENV_DIR
        $PYTHON_PATH -m pip install -r requirements.txt
    fi
}

# Check if virtualenv is installed and setup or setup if not already
if command -v virtualenv &>/dev/null; then
    setup_virtualenv
else
    echo "virtualenv is not installed. Please install it and try again."
    exit 1
fi

# Define functions for various setup tasks
function update_pip() {
    # Upgrade pip and install locked requirements
    $PYTHON_PATH -m pip install --upgrade pip
    $PYTHON_PATH -m pip install -r requirements.txt
}

function migrate() {
    # Apply Django database migrations
    $PYTHON_PATH manage.py migrate
}

function init() {
    # Load initial_data.json fixtures (groups, carriers, types, …)
    $PYTHON_PATH manage.py loaddata initial_data.json
}

function load_testdata() {
    # Queue Celery seeddata task for demo users/packages
    $PYTHON_PATH manage.py seeddata
}

function check() {
    # Run Django deploy checks
    $PYTHON_PATH manage.py check --deploy
}

function processjs() {
    # collectstatic + prune stale hashed JS (manage.py processjs)
    $PYTHON_PATH manage.py processjs
}

# Use case statement to process commands
case "$1" in
    prod)
        update_pip
        migrate
        init
        processjs
        ;;
    dev)
        update_pip
        migrate
        init
        load_testdata
        processjs
        ;;
    update)
        update_pip
        migrate
        processjs
        ;;
    check)
        check
        ;;
    *)
        echo "Available Commands:"
        echo "    check    Run a system check to identify issues for a production instance"
        echo "    dev      Initialize a new development setup"
        echo "    prod     Initialize a new production setup"
        echo "    update   Perform a database migration in preparation for updates"
        ;;
esac
