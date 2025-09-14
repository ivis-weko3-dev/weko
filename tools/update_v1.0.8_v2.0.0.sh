# migrate database from v1.0.8 to v2.0.0
# start postgresql
docker-compose exec -u postgres postgresql pg_ctl start -D /var/lib/postgresql/data

# Input restricted item property id
RESTRICTED_ITEM_PROPERTY_ID=30015

# v1.0.8.sql
docker cp postgresql/update/v1.0.8.sql $(docker-compose ps -q postgresql):/tmp/v1.0.8.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp

# fix_issue_37736.sql
docker cp postgresql/ddl/fix_issue_37736.sql $(docker-compose ps -q postgresql):/tmp/fix_issue_37736.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/fix_issue_37736.sql

# fix_issue_39700.sql
docker cp postgresql/ddl/fix_issue_39700.sql $(docker-compose ps -q postgresql):/tmp/fix_issue_39700.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/fix_issue_39700.sql

# scripts/demo/fix_item_type4.sql (only when using item type 4)
# docker cp scripts/demo/fix_item_type4.sql $(docker-compose ps -q postgresql):/tmp/fix_item_type4.sql
# docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/fix_item_type4.sql

# apply W2023
docker cp "postgresql/ddl/W2023-21 workflow_flow_action_role.sql" $(docker-compose ps -q postgresql):"/tmp/W2023-21 workflow_flow_action_role.sql"
docker-compose exec postgresql psql -U invenio -d invenio -f "/tmp/W2023-21 workflow_flow_action_role.sql"
docker cp "postgresql/ddl/W2023-21 update_resticted_items.sql" $(docker-compose ps -q postgresql):"/tmp/W2023-21 update_resticted_items.sql"
docker-compose exec postgresql psql -U invenio -d invenio -f "/tmp/W2023-21 update_resticted_items.sql"
docker cp "scripts/demo/mail_template.sql" $(docker-compose ps -q postgresql):"/tmp/mail_template.sql"
docker-compose exec postgresql psql -U invenio -d invenio -f "/tmp/mail_template.sql"

# Alembic migration
docker-compose exec web invenio alembic upgrade heads

# scripts/demo/register_properties.py only_specified 
docker-compose exec web invenio shell scripts/demo/register_properties.py only_specified

# scripts/demo/renew_all_item_types.py
docker-compose exec web invenio shell scripts/demo/renew_all_item_types.py;

# scripts/demo/update_feedback_mail_list_to_db.py
docker-compose exec web invenio shell scripts/demo/update_feedback_mail_list_to_db.py

# tools/update_weko_links.py
docker-compose exec web invenio shell tools/update_weko_links.py

# Update resources
docker-compose exec web invenio access allow "files-rest-object-read-version" role "Repository Administrator" role "Community Administrator" role "Contributor"

# Update for shared user ids
docker-compose exec web invenio shell tools/updateRestrictedRecords.py $RESTRICTED_ITEM_PROPERTY_ID

# WOA-06-jsonld_mapping.sql
docker cp postgresql/ddl/WOA-06-jsonld_mapping.sql $(docker-compose ps -q postgresql):/tmp/WOA-06-jsonld_mapping.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/WOA-06-jsonld_mapping.sql
