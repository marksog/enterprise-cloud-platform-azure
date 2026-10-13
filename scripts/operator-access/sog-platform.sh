#!/usr/bin/env bash
set -euo pipefail

SSH_HOST="sog-admin"
LOCAL_DIR="$HOME/.sog-platform"
SSH_PID_FILE="$LOCAL_DIR/ssh-tunnel.pid"

mkdir -p "$LOCAL_DIR"

# --------------------------------------------------
# Helpers
# --------------------------------------------------

valid_pid() {
  [[ "${1:-}" =~ ^[0-9]+$ ]]
}

local_port_free() {
  ! nc -z 127.0.0.1 "$1" 2>/dev/null
}

owned_ssh() {
  local pid="$1"
  valid_pid "$pid" || return 1

  local command
  command=$(ps -p "$pid" -o command= 2>/dev/null) || return 1

  [[ "$command" == *"ssh -N"* &&
     "$command" == *"$SSH_HOST"* &&
     "$command" == *"3000:127.0.0.1:3000"* ]]
}

http_check() {
  local name="$1"
  local url="$2"

  if [[ "$name" == "ArgoCD" ]]; then
    # Local Argo CD uses its internal certificate.
    curl -kfsS --max-time 5 -o /dev/null "$url"
  else
    curl -fsS --max-time 5 -o /dev/null "$url"
  fi
}

# --------------------------------------------------
# Remote Kubernetes port-forwards
# --------------------------------------------------

start_remote() {
  ssh "$SSH_HOST" 'bash -s' <<'REMOTE'
set -euo pipefail

DIR="$HOME/.sog-platform"
mkdir -p "$DIR"

valid_pid() {
  [[ "${1:-}" =~ ^[0-9]+$ ]]
}

owned_forward() {
  local pid="$1"
  local namespace="$2"
  local service="$3"
  local mapping="$4"

  valid_pid "$pid" || return 1

  local command
  command=$(ps -p "$pid" -o args= 2>/dev/null) || return 1

  [[ "$command" == *"kubectl port-forward"* &&
     "$command" == *"-n $namespace"* &&
     "$command" == *"svc/$service"* &&
     "$command" == *"$mapping"* ]]
}

port_open() {
  (echo > /dev/tcp/127.0.0.1/"$1") >/dev/null 2>&1
}

start_forward() {
  local name="$1"
  local namespace="$2"
  local service="$3"
  local mapping="$4"
  local port="${mapping%%:*}"
  local pid=""

  echo "Checking $name..."

  if [[ -f "$DIR/$name.pid" ]]; then
    pid=$(cat "$DIR/$name.pid")

    if owned_forward "$pid" "$namespace" "$service" "$mapping"; then
      if port_open "$port"; then
        echo "$name already running"
        return 0
      fi

      echo "Restarting unhealthy $name"
      kill "$pid" 2>/dev/null || true
    fi

    rm -f "$DIR/$name.pid"
  fi

  # Do not interfere with unrelated processes.
  if port_open "$port"; then
    echo "ERROR: port $port is occupied by another process." >&2
    return 1
  fi

  nohup kubectl port-forward \
    --address 127.0.0.1 \
    -n "$namespace" \
    "svc/$service" \
    "$mapping" \
    > "$DIR/$name.log" 2>&1 < /dev/null &

  pid=$!
  echo "$pid" > "$DIR/$name.pid"

  # Wait until Kubernetes has established the listener.
  for attempt in {1..15}; do
    if ! owned_forward "$pid" "$namespace" "$service" "$mapping"; then
      echo "ERROR: $name exited unexpectedly." >&2
      cat "$DIR/$name.log" >&2
      rm -f "$DIR/$name.pid"
      return 1
    fi

    if port_open "$port"; then
      echo "$name started successfully"
      return 0
    fi

    sleep 1
  done

  echo "ERROR: $name failed readiness check." >&2
  kill "$pid" 2>/dev/null || true
  rm -f "$DIR/$name.pid"
  return 1
}

start_forward grafana \
  sog-nonprod-observability \
  sog-observability-grafana \
  3000:80

start_forward prometheus \
  sog-nonprod-observability \
  sog-observability-kube-pro-prometheus \
  9090:9090

start_forward alertmanager \
  sog-nonprod-observability \
  sog-observability-kube-pro-alertmanager \
  9093:9093

start_forward argocd \
  argocd \
  argocd-server \
  8080:443
REMOTE
}

# --------------------------------------------------
# Local SSH tunnel
# --------------------------------------------------

start_local() {
  local pid=""

  if [[ -f "$SSH_PID_FILE" ]]; then
    pid=$(cat "$SSH_PID_FILE")

    if owned_ssh "$pid"; then
      if http_check Prometheus \
        http://127.0.0.1:9090/-/ready; then
        echo "SSH tunnel already running"
        return 0
      fi

      echo "Restarting unhealthy SSH tunnel"
      kill "$pid" 2>/dev/null || true
    fi

    rm -f "$SSH_PID_FILE"
  fi

  for port in 3000 9090 9093 8080; do
    if ! local_port_free "$port"; then
      echo "ERROR: local port $port is already occupied." >&2
      return 1
    fi
  done

  ssh -N \
    -o ExitOnForwardFailure=yes \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -L 3000:127.0.0.1:3000 \
    -L 9090:127.0.0.1:9090 \
    -L 9093:127.0.0.1:9093 \
    -L 8080:127.0.0.1:8080 \
    "$SSH_HOST" \
    > "$LOCAL_DIR/ssh-tunnel.log" 2>&1 &

  pid=$!
  echo "$pid" > "$SSH_PID_FILE"

  for attempt in {1..15}; do
    if ! owned_ssh "$pid"; then
      echo "ERROR: SSH tunnel exited unexpectedly." >&2
      cat "$LOCAL_DIR/ssh-tunnel.log" >&2
      rm -f "$SSH_PID_FILE"
      return 1
    fi

    if http_check Prometheus \
      http://127.0.0.1:9090/-/ready; then
      echo "SSH tunnel started successfully"
      return 0
    fi

    sleep 1
  done

  echo "ERROR: SSH tunnel failed health check." >&2
  kill "$pid" 2>/dev/null || true
  rm -f "$SSH_PID_FILE"
  return 1
}

# --------------------------------------------------
# Status
# --------------------------------------------------

status() {
  echo
  echo "SOG Platform Operator Access"
  echo "----------------------------"

  if [[ -f "$SSH_PID_FILE" ]] &&
     owned_ssh "$(cat "$SSH_PID_FILE")"; then
    echo "SSH tunnel: Running"
  else
    echo "SSH tunnel: Stopped"
  fi

  echo
  echo "Application health:"

  if http_check Grafana http://127.0.0.1:3000/login; then
    echo "Grafana: Healthy"
  else
    echo "Grafana: Unavailable"
  fi

  if http_check Prometheus http://127.0.0.1:9090/-/ready; then
    echo "Prometheus: Healthy"
  else
    echo "Prometheus: Unavailable"
  fi

  if http_check Alertmanager http://127.0.0.1:9093/-/ready; then
    echo "Alertmanager: Healthy"
  else
    echo "Alertmanager: Unavailable"
  fi

  if http_check ArgoCD https://127.0.0.1:8080/; then
    echo "Argo CD: Healthy"
  else
    echo "Argo CD: Unavailable"
  fi
}

# --------------------------------------------------
# Stop
# --------------------------------------------------

stop_local() {
  if [[ -f "$SSH_PID_FILE" ]]; then
    local pid
    pid=$(cat "$SSH_PID_FILE")

    if owned_ssh "$pid"; then
      kill "$pid" 2>/dev/null || true
      echo "SSH tunnel stopped"
    fi

    rm -f "$SSH_PID_FILE"
  fi
}

stop_remote() {
  ssh "$SSH_HOST" 'bash -s' <<'REMOTE'
set -euo pipefail

DIR="$HOME/.sog-platform"

stop_forward() {
  local name="$1"
  local namespace="$2"
  local service="$3"
  local mapping="$4"
  local file="$DIR/$name.pid"

  [[ -f "$file" ]] || return 0

  local pid command
  pid=$(cat "$file")

  if [[ "$pid" =~ ^[0-9]+$ ]]; then
    command=$(ps -p "$pid" -o args= 2>/dev/null || true)

    if [[ "$command" == *"kubectl port-forward"* &&
          "$command" == *"-n $namespace"* &&
          "$command" == *"svc/$service"* &&
          "$command" == *"$mapping"* ]]; then
      kill "$pid" 2>/dev/null || true
      echo "Stopped $name"
    fi
  fi

  rm -f "$file"
}

stop_forward grafana \
  sog-nonprod-observability \
  sog-observability-grafana \
  3000:80

stop_forward prometheus \
  sog-nonprod-observability \
  sog-observability-kube-pro-prometheus \
  9090:9090

stop_forward alertmanager \
  sog-nonprod-observability \
  sog-observability-kube-pro-alertmanager \
  9093:9093

stop_forward argocd \
  argocd \
  argocd-server \
  8080:443
REMOTE
}

# --------------------------------------------------
# Main
# --------------------------------------------------

case "${1:-}" in
  start)
    start_remote
    start_local
    status
    ;;

  status)
    status
    ;;

  stop)
    stop_local
    stop_remote
    echo "Operator access stopped"
    ;;

  *)
    echo "Usage: sog-platform.sh {start|status|stop}"
    exit 1
    ;;
esac