#!/bin/bash

# Allow for custom venv names while defaulting to env if none is provided
if [ "$2" != "" ]
then
    VENV_DIR="$2"
else
    VENV_DIR="env"
fi

PYTHON_PATH="$VENV_DIR/bin/python3"

function setup_virtualenv() {
    if [ ! -d "$VENV_DIR" ]; then
        echo "Setting up the virtual environment..."
        virtualenv $VENV_DIR
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
function migrate() {
    $PYTHON_PATH manage.py migrate
}

function init() {
    $PYTHON_PATH manage.py loaddata initial_data.json
}

function load_testdata() {
    $PYTHON_PATH manage.py loaddata package_seed_data.json
}

function check() {
    $PYTHON_PATH manage.py check --deploy
}

function collectstatic() {
    $PYTHON_PATH manage.py collectstatic --no-input
}

# Use case statement to process commands
case "$1" in
    prod)
        migrate
        init
        collectstatic
        ;;
    dev)
        migrate
        init
        load_testdata
        collectstatic
        ;;
    update)
        migrate
        collectstatic
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
