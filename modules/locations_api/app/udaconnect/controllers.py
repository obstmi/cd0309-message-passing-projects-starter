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
from kafka import KafkaProducer
import json
import logging

DATE_FORMAT = "%Y-%m-%d"

api = Namespace("UdaConnect", description="Connections via geolocation.")  # noqa

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("udaconnect-api")

# TODO: This needs better exception handling

# configure Kafka-producer
producer = KafkaProducer(
    bootstrap_servers='kafka-service:9092',
    key_serializer=lambda k: k.encode('utf-8'),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)
@api.route("/locations")
@api.route("/locations/<location_id>")
@api.param("location_id", "Unique ID for a given Location", _in="query")
class LocationResource(Resource):
    @accepts(schema=LocationSchema)
    def post(self):
        location_data = request.get_json()
        logger.info(f"Received location data: {location_data}")

        # send message to Kafka
        try:
            logger.info("Sending message to Kafka")
            producer.send(
                "locations",
                key=str(location_data["person_id"]),
                value=location_data
            )
            producer.flush()
            logger.info("Message sent to Kafka successfully")
            return {"message": "Location request received"}, 202  # 202 Accepted
        except Exception as e:
            logger.error(f"Failed to send message to Kafka: {str(e)}")
            return {"message": f"Failed to send message to Kafka: {str(e)}"}, 500  # 500 Internal Server Error
    @responds(schema=LocationSchema)
    def get(self, location_id) -> Location:
        location: Location = LocationService.retrieve(location_id)
        return location

