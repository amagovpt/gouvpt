#!/bin/bash
docker-compose up -d
source venv/bin/activate
export FLASK_DEBUG=True
#udata worker start &
udata serve