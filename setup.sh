#!/bin/bash

function migrate () {
    python3 manage.py migrate
}

function init () {
    python3 manage.py loaddata initial_data.json
}

function load_testdata () {
    python3 manage.py loaddata package_seed_data.json
}

function check () {
    python3 manage.py check --deploy
}

function collectstatic () {
    python3 manage.py collectstatic --no-input
}

if [ "$2" != "" ]
then
  source $2/bin/activate
fi

if [ "$1" = "prod" ]
then
  migrate
  init
  collectstatic
elif [ "$1" = "dev" ]
then
  migrate
  init
  load_testdata
  collectstatic
elif [ "$1" = "update" ]
then
  migrate
  collectstatic
elif [ "$1" = "check" ]
then
  check
else
  echo "Available Commands:"
  echo "    check    Run a system check to indentity issues for a production instance"
  echo "    dev      Initialize a new development setup"
  echo "    prod     Initialize a new production setup"
  echo "    update   Perform a database migration in preparation for updates"
fi
