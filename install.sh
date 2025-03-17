#!/bin/bash

find . | grep -E "(__pycache__|\.eggs|\.pyc|\.pyo$)" | xargs rm -rf
docker compose down -v
for volume in $(docker volume ls -f name=weko -q); do
  docker volume rm $(volume)
done
DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker compose build --no-cache --force-rm

# Initialize resources
docker-compose run --rm web ./scripts/populate-instance.sh
docker cp scripts/demo/item_type4.sql $(docker-compose ps -q postgresql):/tmp/item_type.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/item_type.sql
docker cp scripts/demo/indextree.sql $(docker-compose ps -q postgresql):/tmp/indextree.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/indextree.sql
docker-compose run --rm web invenio workflow init action_status,Action
docker cp scripts/demo/defaultworkflow.sql $(docker-compose ps -q postgresql):/tmp/defaultworkflow.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/defaultworkflow.sql
docker cp scripts/demo/doi_identifier.sql $(docker-compose ps -q postgresql):/tmp/doi_identifier.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/doi_identifier.sql

docker-compose -f run --rm web invenio webpack create
docker-compose -f run --rm web invenio collect -v
docker-compose -f run --rm web invenio webpack build

# Start services
docker compose up -d
