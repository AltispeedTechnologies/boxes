#!/bin/bash
# Bootstrap and maintain a Boxes install.
#
# Usage:
#   ./setup.sh prod [venv_dir]
#   ./setup.sh dev [venv_dir]
#   ./setup.sh update [venv_dir]
#   ./setup.sh reset [venv_dir]   # flush DB + fixtures (clean instance, no bulk seed)
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

ensure_system() {
    # Inactive system actor used by automated ledger / on_delete reassignment
    $PYTHON_PATH manage.py shell -c "from boxes.backend.system import ensure_system_user; ensure_system_user(); print('system user ready')"
    $PYTHON_PATH manage.py bootstrap_demo
}

load_testdata() {
    # Prefer synchronous seed so reset/dev works without a running Celery worker
    $PYTHON_PATH manage.py seeddata --sync
}

flush_db() {
    echo "Flushing database (all application data)..."
    $PYTHON_PATH manage.py flush --no-input
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
    $PYTHON_PATH -m coverage report --fail-under=55
}

case "$1" in
    prod)
        update_pip
        migrate
        init
        ensure_system
        processjs
        ;;
    dev)
        update_pip
        install_dev
        migrate
        init
        ensure_system
        load_testdata
        processjs
        ;;
    reset)
        # Clean instance: wipe all rows, reload fixtures, no bulk Faker seed.
        # Demo logins from initial_data.json: sysadmin / staff / customer (changem3).
        update_pip
        install_dev
        migrate
        flush_db
        migrate
        init
        ensure_system
        processjs
        echo "Database reset complete (fixtures only; no seeddata)."
        echo "Logins: sysadmin, staff, customer — password changem3"
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
        echo "Usage: $0 {prod|dev|reset|update|check|test|test-coverage} [venv_dir]"
        echo
        echo "Commands:"
        echo "    prod            Production setup (migrate + fixtures + static)"
        echo "    dev             Development setup (includes seed data and dev deps)"
        echo "    reset           Flush DB and reload fixtures only (clean working instance)"
        echo "    update          Upgrade packages, migrate, process static"
        echo "    check           Django deploy checks"
        echo "    test            Run unit tests"
        echo "    test-coverage   Run tests with coverage (fail under 55%)"
        exit 1
        ;;
esac
