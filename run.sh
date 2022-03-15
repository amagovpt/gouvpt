#!/bin/bash
docker-compose -f docker-compose-dev.yml up -d
source venv/bin/activate
export FLASK_DEBUG=True
udata worker start &
udata serve