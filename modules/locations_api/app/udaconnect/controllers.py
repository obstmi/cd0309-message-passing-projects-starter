from datetime import datetime

from app.udaconnect.models import Location, Person
from app.udaconnect.schemas import (
    LocationSchema
)
from app.udaconnect.services import LocationService
from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from typing import Optional, List
from confluent_kafka import Producer
import json

DATE_FORMAT = "%Y-%m-%d"

api = Namespace("UdaConnect", description="Connections via geolocation.")  # noqa


# TODO: This needs better exception handling

# Kafka-Producer konfigurieren
producer = Producer({'bootstrap.servers': 'kafka-service:9092'})
@api.route("/locations")
@api.route("/locations/<location_id>")
@api.param("location_id", "Unique ID for a given Location", _in="query")
class LocationResource(Resource):
    @accepts(schema=LocationSchema)
    @responds(schema=LocationSchema)
    def post(self):
        location_data = request.get_json()

        # Location in Kafka-Topic senden
        producer.produce("locations", key=str(location_data["person_id"]), value=json.dumps(location_data))
        producer.flush()

        return {"message": "Location request received"}, 202  # 202 Accepted

    @responds(schema=LocationSchema)
    def get(self, location_id) -> Location:
        location: Location = LocationService.retrieve(location_id)
        return location

