#!/bin/bash
#
# Run locust load test
#
#####################################################################
ARGS="$@"
HOST="${1}"
FILE="${6}"
SCRIPT_NAME=`basename "$0"`
INITIAL_DELAY=1
TARGET_HOST="$HOST"
USERS="${7}"
RUNTIME=10
SPAWN_RATE="${8}"
SCENARIO="${9}"


do_check() {

  # Check hostname is not empty
  if [ "${TARGET_HOST}x" == "x" ]; then
    echo "TARGET_HOST is not set; use '-h hostname:port'"
    exit 1xf
  fi

  # Check for locust
  if [ ! `command -v locust` ]; then
    echo "Python 'locust' package is not found!"
    exit 1
  fi

  # Check scenario
  if [ "$SCENARIO" == "scenario_A" ]; then
    LOCUST_FILE="./load-test/sockshop_scenario_a_locust.py"
    echo "Scenario A: Using Locust file $LOCUST_FILE"
  elif [ "$SCENARIO" == "scenario_B" ]; then
    LOCUST_FILE="./load-test/sockshop_scenario_b_locust.py"
    echo "Scenario B: Using Locust file $LOCUST_FILE"
  else
    LOCUST_FILE="./load-test/locustfile.py"
    echo "Default Locust file: $LOCUST_FILE"
  fi
}

do_exec() {
  sleep $INITIAL_DELAY

  # Check if host is running
  # STATUS=$(curl -s -o /dev/null -w "%{http_code}" ${TARGET_HOST}) 
  # if [ $STATUS -ne 200 ]; then
  #     echo "${TARGET_HOST} is not accessible"
  #     exit 1
  # fi

  echo "Will run $LOCUST_FILE against $TARGET_HOST. Spawning $USERS users."
  locust --host=http://$TARGET_HOST -f $LOCUST_FILE --users=$USERS --spawn-rate=$SPAWN_RATE --csv=$FILE --headless --only-summary 
  echo "done"
}

do_usage() {
    cat >&2 <<EOF
Usage:
  ${SCRIPT_NAME} [ hostname ] OPTIONS

Options:
  -d  Delay before starting
  -h  Target host url, e.g. http://localhost/ - specify only the IP of the host (no http and /)
      We run: ./runLocust.sh -h 145.108.225.16:9099
  -c  Number of users (default 2)
  -r  Duration of RUNTIME (default 10)
  -l  Load FILE

Description:
  Runs a Locust load simulation against specified host.

EOF
  exit 1
}



while getopts ":d:h:c:r:l:u:s:n:" o; do
  case "${o}" in
    d)
        INITIAL_DELAY=${OPTARG}
        #echo $INITIAL_DELAY
        ;;
    h)
        TARGET_HOST=${OPTARG}
        echo $TARGET_HOST
        ;;
    u)
        USERS=${OPTARG:-2}
        #echo $USERS
        ;;
    r)
        RUNTIME=${OPTARG:-10}
        #echo $RUNTIME
        ;;
    l) 
        FILE=${OPTARG:-18}
        echo $FILE
        ;;
    u) 
        USERS=${OPTARG:-26}
        echo $USERS
        ;;
    s) 
        SPAWN_RATE=${OPTARG:-34}
        echo $SPAWN_RATE
        ;;
    n) 
        SCENARIO=${OPTARG:-42}
        echo $SCENARIO
        ;;
    *)
        do_usage
        ;;
  esac
done


do_check
do_exec
