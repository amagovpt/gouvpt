#!/bin/bash
docker-compose up -d
source venv3/bin/activate
export FLASK_DEBUG=True
udata worker start &
udata serve