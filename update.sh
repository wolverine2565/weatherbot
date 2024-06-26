#!/bin/bash

cd /home/admin


REPO_URL="https://github.com/wolverine2565/weatherbot"
DEST_DIR="/home/admin/weatherbot"

if [ -d "$DEST_DIR" ]; then
        echo "directory already exits, and will be removed"
    rm -rf $DEST_DIR
fi

git clone $REPO_URL $DEST_DIR

if [ $? -eq 0 ]; then
        echo    "repo cloned succefull"
else
        echo    "repo clone error"
fi

VENV_PATH="/home/admin/weatherbot"

virtualenv $VENV_PATH/venv

if [ $? -eq 0 ]; then
        echo "A virtual environment created"
else
        echo "A virtual environment creation error"
fi

source $VENV_PATH/venv/bin/activate
if [ $? -eq 0 ]; then
        echo "A virtual environment activated"
else
        echo "A virtual environment activation error"
fi


FILE_PATH="/home/admin/weatherbot/settings/database_config.py"

echo "url = 'postgresql://postgres:admin123@db:5432/postgres'" > $FILE_PATH

if [ $? -eq 0 ]; then
    echo "database_config.py created"
else
    echo "database_config.py creation error"
fi


cd /home/admin/weatherbot

docker build -t bot .

docker-compose up --build

function build_and_run_containers() {
    docker-compose up --build
}

#build and run containers
build_and_run_containers

while [ $? -ne 0 ]; do
    echo "One or more containers have exited with an error. Rebuilding and restarting all containers..."
    sleep 5
    build_and_run_containers
done
