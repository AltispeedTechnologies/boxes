#!/bin/bash
# Bootstrap and maintain a Boxes install.
#
# Usage:
#   ./setup.sh prod [venv_dir]
#   ./setup.sh dev [venv_dir]
#   ./setup.sh update [venv_dir]
#   ./setup.sh check [venv_dir]
#   ./setup.sh test [venv_dir]
#   ./setup.sh test-coverage [venv_dir]
#
# Optional second argument sets the virtualenv directory (default: env).
# Load environment from /etc/boxes.env (or ENV_PATH) before Django commands.

if [ "$2" != "" ]; then
    VENV_DIR="$2"
else
    VENV_DIR="env"
fi

PYTHON_PATH="$VENV_DIR/bin/python3"

setup_virtualenv() {
    if [ ! -d "$VENV_DIR" ]; then
        echo "Setting up the virtual environment..."
        virtualenv "$VENV_DIR"
        $PYTHON_PATH -m pip install -r requirements.txt
    fi
}

if command -v virtualenv &>/dev/null; then
    setup_virtualenv
else
    echo "virtualenv is not installed. Please install it and try again."
    exit 1
fi

update_pip() {
    $PYTHON_PATH -m pip install --upgrade pip
    $PYTHON_PATH -m pip install -r requirements.txt
}

install_dev() {
    if [ -f requirements-dev.txt ]; then
        $PYTHON_PATH -m pip install -r requirements-dev.txt
    fi
}

migrate() {
    $PYTHON_PATH manage.py migrate
}

init() {
    $PYTHON_PATH manage.py loaddata initial_data.json
}

load_testdata() {
    $PYTHON_PATH manage.py seeddata
}

check() {
    $PYTHON_PATH manage.py check --deploy
}

processjs() {
    $PYTHON_PATH manage.py processjs
}

run_tests() {
    install_dev
    $PYTHON_PATH manage.py test boxes.tests
}

run_coverage() {
    install_dev
    $PYTHON_PATH -m coverage run manage.py test boxes.tests
    $PYTHON_PATH -m coverage report --fail-under=40
}

case "$1" in
    prod)
        update_pip
        migrate
        init
        processjs
        ;;
    dev)
        update_pip
        install_dev
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
    test)
        run_tests
        ;;
    test-coverage)
        run_coverage
        ;;
    *)
        echo "Available Commands:"
        echo "    check           Production deploy checks"
        echo "    dev             Development setup (includes seed data and dev deps)"
        echo "    prod            Production setup"
        echo "    update          Upgrade deps, migrate, refresh static JS"
        echo "    test            Run unit tests"
        echo "    test-coverage   Run unit tests under coverage"
        ;;
esac
