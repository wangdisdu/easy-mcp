#!/bin/sh

DIR=$(cd "$(dirname "$0")" && pwd)
cd $DIR

HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
LOG_CONFIG=api/logging.ini
APP=api.main:app

mkdir -p logs

uvicorn $APP --host $HOST --port $PORT --log-config $LOG_CONFIG
