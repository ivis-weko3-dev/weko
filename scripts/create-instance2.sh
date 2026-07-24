#!/usr/bin/env bash
# shellcheck disable=SC2103,SC2102
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

# check environment variables:
if [ "${INVENIO_WEB_HOST}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_WEB_HOST before runnning this script."
    echo "[ERROR] Example: export INVENIO_WEB_HOST=192.168.50.10"
    exit 1
fi
if [ "${INVENIO_WEB_INSTANCE}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_WEB_INSTANCE before runnning this script."
    echo "[ERROR] Example: export INVENIO_WEB_INSTANCE=invenio"
    exit 1
fi
if [ "${INVENIO_WEB_VENV}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_WEB_VENV before runnning this script."
    echo "[ERROR] Example: export INVENIO_WEB_VENV=invenio"
    exit 1
fi
if [ "${INVENIO_WEB_HOST_NAME}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_WEB_HOST_NAME before runnning this script."
    echo "[ERROR] Example: export INVENIO_WEB_HOST_NAME=invenio"
    exit 1
fi
if [ "${INVENIO_USER_EMAIL}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_USER_EMAIL before runnning this script."
    echo "[ERROR] Example: export INVENIO_USER_EMAIL=wekosoftware@nii.ac.jp"
    exit 1
fi
if [ "${INVENIO_USER_PASS}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_USER_PASS before runnning this script."
    echo "[ERROR] Example: export INVENIO_USER_PASS=uspass123"
    exit 1
fi
if [ "${INVENIO_POSTGRESQL_HOST}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_POSTGRESQL_HOST before runnning this script."
    echo "[ERROR] Example: export INVENIO_POSTGRESQL_HOST=192.168.50.11"
    exit 1
fi
if [ "${INVENIO_POSTGRESQL_DBNAME}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_POSTGRESQL_DBNAME before runnning this script."
    echo "[ERROR] Example: INVENIO_POSTGRESQL_DBNAME=invenio"
    exit 1
fi
if [ "${INVENIO_POSTGRESQL_DBUSER}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_POSTGRESQL_DBUSER before runnning this script."
    echo "[ERROR] Example: INVENIO_POSTGRESQL_DBUSER=invenio"
    exit 1
fi
if [ "${INVENIO_POSTGRESQL_DBPASS}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_POSTGRESQL_DBPASS before runnning this script."
    echo "[ERROR] Example: INVENIO_POSTGRESQL_DBPASS=dbpass123"
    exit 1
fi
if [ "${INVENIO_REDIS_HOST}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_REDIS_HOST before runnning this script."
    echo "[ERROR] Example: export INVENIO_REDIS_HOST=192.168.50.12"
    exit 1
fi
if [ "${INVENIO_ELASTICSEARCH_HOST}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_ELASTICSEARCH_HOST before runnning this script."
    echo "[ERROR] Example: export INVENIO_ELASTICSEARCH_HOST=192.168.50.13"
    exit 1
fi
if [ "${INVENIO_RABBITMQ_HOST}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_RABBITMQ_HOST before runnning this script."
    echo "[ERROR] Example: export INVENIO_RABBITMQ_HOST=192.168.50.14"
    exit 1
fi
if [ "${INVENIO_RABBITMQ_USER}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_RABBITMQ_USER before runnning this script."
    echo "[ERROR] Example: export INVENIO_RABBITMQ_USER=guest"
    exit 1
fi
if [ "${INVENIO_RABBITMQ_PASS}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_RABBITMQ_PASS before runnning this script."
    echo "[ERROR] Example: export INVENIO_RABBITMQ_PASS=guest"
    exit 1
fi
if [ "${INVENIO_RABBITMQ_VHOST}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_RABBITMQ_VHOST before runnning this script."
    echo "[ERROR] Example: export INVENIO_RABBITMQ_VHOST=/"
    exit 1
fi
if [ "${INVENIO_WORKER_HOST}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_WORKER_HOST before runnning this script."
    echo "[ERROR] Example: export INVENIO_WORKER_HOST=192.168.50.15"
    exit 1
fi

system_python="$(command -v python3.12 || command -v python3 || true)"
if [ -z "$system_python" ]; then
    echo "[ERROR] python3.12 (or python3) is required before running this script."
    exit 1
fi

# sphinxdoc-create-virtual-environment-begin
if [ ! -f "$VIRTUAL_ENV/bin/activate" ]; then
    UV_PYTHON_DOWNLOADS=never uv venv --python "$system_python" "$VIRTUAL_ENV"
fi
source "$VIRTUAL_ENV/bin/activate"
cd "$VIRTUAL_ENV"
# sphinxdoc-create-virtual-environment-end

# Some runtime deps still import pkg_resources, which is provided by setuptools.
if ! python -c "import pkg_resources" > /dev/null 2>&1; then
    uv pip install "setuptools==71.0.3"
fi

# quit on errors and unbound symbols:
set -o errexit
set -o nounset


# sphinxdoc-customise-instance-begin
mkdir -p "var/instance/"
mkdir -p "var/instance/data"
mkdir -p "var/instance/conf"
mkdir -p "var/instance/static"
jinja2 "/code/scripts/instance.cfg" > "var/instance/conf/${INVENIO_WEB_INSTANCE}.cfg"
ln -s "$(pwd)/var/instance/conf/${INVENIO_WEB_INSTANCE}.cfg" "var/instance/${INVENIO_WEB_INSTANCE}.cfg"
cp -pf "/code/scripts/uwsgi.ini" "var/instance/conf/"
cp -pf "/code/modules/weko-theme/weko_theme/assets/bootstrap3/css/weko_theme/_variables.scss" "var/instance/data/"
cp -prf "/code/modules/weko-index-tree/weko_index_tree/static/indextree" "var/instance/data/"
# sphinxdoc-customise-instance-end

# sphinxdoc-run-npm-begin
${INVENIO_WEB_INSTANCE} webpack create
cd "$VIRTUAL_ENV/var/instance/assets"
CI=true npm install --legacy-peer-deps
CI=true npm install angular-schema-form@0.8.13 --legacy-peer-deps
## for install ckeditor plugins
cd "$VIRTUAL_ENV/var/instance/assets/node_modules/ckeditor/plugins"
CI=true git clone https://github.com/RCOSDP/base64image.git
# sphinxdoc-run-npm-end
cd "$VIRTUAL_ENV/var/instance/assets/node_modules"
rm -rf invenio-search-js
git clone --branch feature/changePaginationForSearchAfterUse https://github.com/RCOSDP/invenio-search-js.git

cd "$VIRTUAL_ENV/var/instance/assets"
ln -s ../static/templates templates
# force copy webpack.config.js to NODE_ENV=production
\cp -pf "/code/scripts/webpack.config.js" "$(pwd)/build/webpack.config.js"
# sphinxdoc-collect-and-build-assets-begin
${INVENIO_WEB_INSTANCE} collect -v
${INVENIO_WEB_INSTANCE} webpack build
# sphinxdoc-collect-and-build-assets-end

# gunicorn uwsgi - begin
# pip install gunicorn
# pip install meinheld
uv pip install "uwsgi>=2.0.31,<3"
uv pip install "uwsgitop>=0.12,<1"
# gunicorn uwsgi -end

# clean caches
uv cache clean
CI=true npm cache clean --force
