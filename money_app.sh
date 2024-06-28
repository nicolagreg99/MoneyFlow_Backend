#!/bin/bash

APP_NAME="money_app"
APP_DIR=$(dirname $(realpath $0))
VENV_DIR="$APP_DIR/venv"
APP_SCRIPT="$APP_DIR/app.py"
LOG_FILE="$APP_DIR/$APP_NAME.log"
PID_FILE="$APP_DIR/$APP_NAME.pid"

start() {
    echo "Starting $APP_NAME..."
    source $VENV_DIR/bin/activate
    nohup python3 $APP_SCRIPT >> $LOG_FILE 2>&1 &
    echo $! > $PID_FILE
    echo "$APP_NAME started with PID $(cat $PID_FILE)"
}

stop() {
    echo "Stopping $APP_NAME..."
    if [ -f $PID_FILE ]; then
        kill $(cat $PID_FILE)
        rm $PID_FILE
        echo "$APP_NAME stopped"
    else
        echo "PID file not found"
    fi
}

restart() {
    echo "Restarting $APP_NAME..."
    stop
    start
}

foreground() {
    echo "Running $APP_NAME in foreground..."
    source $VENV_DIR/bin/activate
    python3 $APP_SCRIPT
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    foreground)
        foreground
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|foreground}"
        ;;
esac
