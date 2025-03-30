#!/bin/sh

flask run --host=0.0.0.0 --port=5000 &
python -m app.udaconnect.grpc_server