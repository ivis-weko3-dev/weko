#!/usr/bin/env bash
set -euo pipefail

PGPOOL_CONF=${PGPOOL_CONF:-/etc/pgpool2/pgpool.conf}
PCP_CONF=${PCP_CONF:-/etc/pgpool2/pcp.conf}
POOL_PASSWD=${POOL_PASSWD:-/etc/pgpool2/pool_passwd}

backend_host=${PGPOOL_PARAMS_BACKEND_HOSTNAME0:-postgresql}
backend_port=${PGPOOL_PARAMS_BACKEND_PORT0:-5432}
backend_weight=${PGPOOL_PARAMS_BACKEND_WEIGHT0:-1}
pgpool_port=${PGPOOL_PARAMS_PORT:-5432}

postgres_user=${PGPOOL_POSTGRES_USERNAME:-invenio}
postgres_password=${PGPOOL_POSTGRES_PASSWORD:-dbpass123}

sr_check_user=${PGPOOL_PARAMS_SR_CHECK_USER:-$postgres_user}
sr_check_password=${PGPOOL_PARAMS_SR_CHECK_PASSWORD:-$postgres_password}

admin_user=${PGPOOL_ADMIN_USERNAME:-admin}
admin_password=${PGPOOL_ADMIN_PASSWORD:-adminpass}

client_idle_limit=${PGPOOL_CLIENT_IDLE_LIMIT:-300}
connection_life_time=${PGPOOL_CONNECTION_LIFE_TIME:-10}
num_init_children=${PGPOOL_NUM_INIT_CHILDREN:-2}
max_pool=${PGPOOL_MAX_POOL:-2}

mkdir -p /etc/pgpool2 /var/run/pgpool /var/log/pgpool

cat > "$PGPOOL_CONF" <<EOF
listen_addresses = '*'
port = ${pgpool_port}
socket_dir = '/var/run/pgpool'
pcp_listen_addresses = '*'
pcp_port = 9898
pcp_socket_dir = '/var/run/pgpool'

backend_clustering_mode = 'streaming_replication'
backend_hostname0 = '${backend_host}'
backend_port0 = ${backend_port}
backend_weight0 = ${backend_weight}
backend_data_directory0 = '/var/lib/postgresql/data'
backend_flag0 = 'ALLOW_TO_FAILOVER'

enable_pool_hba = off
pool_passwd = '${POOL_PASSWD}'

authentication_timeout = 60

sr_check_period = 10
sr_check_user = '${sr_check_user}'
sr_check_password = '${sr_check_password}'
health_check_period = 10
health_check_user = '${sr_check_user}'
health_check_password = '${sr_check_password}'

num_init_children = ${num_init_children}
max_pool = ${max_pool}
client_idle_limit = ${client_idle_limit}
connection_life_time = ${connection_life_time}

log_destination = 'stderr'
logging_collector = off
pid_file_name = '/var/run/pgpool/pgpool.pid'
logdir = '/tmp'
EOF

admin_md5=$(printf '%s' "$admin_password" | md5sum | awk '{print $1}')
printf '%s:%s\n' "$admin_user" "$admin_md5" > "$PCP_CONF"
chmod 600 "$PCP_CONF"

pg_md5_user_hash() {
  local user="$1"
  local pass="$2"
  local user_hash
  user_hash=$(printf '%s%s' "$pass" "$user" | md5sum | awk '{print $1}')
  printf '%s:md5%s\n' "$user" "$user_hash"
}

{
  pg_md5_user_hash "$postgres_user" "$postgres_password"
  if [[ "$sr_check_user" != "$postgres_user" ]]; then
    pg_md5_user_hash "$sr_check_user" "$sr_check_password"
  fi
} > "$POOL_PASSWD"
chmod 600 "$POOL_PASSWD"

exec /usr/local/bin/pgpool -n -f "$PGPOOL_CONF" -F "$PCP_CONF"

