import logging
import json
import threading
import signal
from confluent_kafka import Consumer, KafkaError
from datetime import datetime, timedelta
from typing import Dict, List

from app import db
from app.udaconnect.models import Location, Person
from app.udaconnect.schemas import LocationSchema
from geoalchemy2.functions import ST_AsText, ST_Point
from sqlalchemy.sql import text

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("udaconnect-api")

stop_event = threading.Event()

def signal_handler(sig, frame):
    logger.info("Shutdown signal received. Stopping Kafka Consumer...")
    stop_event.set()

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

class LocationService:
    @staticmethod
    def retrieve(location_id) -> Location:
        location, coord_text = (
            db.session.query(Location, Location.coordinate.ST_AsText())
            .filter(Location.id == location_id)
            .one()
        )

        # Rely on database to return text form of point to reduce overhead of conversion in app code
        location.wkt_shape = coord_text
        return location

    @staticmethod
    def create(location: Dict) -> Location:
        validation_results: Dict = LocationSchema().validate(location)
        if validation_results:
            logger.warning(f"Unexpected data format in payload: {validation_results}")
            raise Exception(f"Invalid payload: {validation_results}")

        new_location = Location()
        new_location.person_id = location["person_id"]
        new_location.creation_time = location["creation_time"]
        new_location.coordinate = ST_Point(location["latitude"], location["longitude"])
        db.session.add(new_location)
        db.session.commit()

        return new_location
    
    @staticmethod
    def start_kafka_consumer():
        """
        Start the Kafka-Consumer in a separate thread.
        """
        def consume():
            consumer = Consumer({
                'bootstrap.servers': 'kafka-service:9092',
                'group.id': 'location-consumer-group',
                'auto.offset.reset': 'earliest',
                'enable.auto.commit': False,  # Manuelles Commit
                'session.timeout.ms': 10000,
                'max.poll.interval.ms': 300000
            })
            consumer.subscribe(['locations'])

            logger.info("Kafka Consumer started...")

            try:
                while not stop_event.is_set():
                    msg = consumer.poll(1.0)
                    if msg is None:
                        continue
                    if msg.error():
                        if msg.error().code() == KafkaError._PARTITION_EOF:
                            logger.info(f"End of partition reached {msg.topic()} [{msg.partition()}]")
                        elif msg.error().code() == KafkaError._ALL_BROKERS_DOWN:
                            logger.critical("All Kafka brokers are down!")
                            break
                        else:
                            logger.error(f"Kafka error: {msg.error()}")
                        continue

                    try:
                        location_data = json.loads(msg.value().decode('utf-8'))
                        logger.info(f"Received message: {location_data}")
                        LocationService.create(location_data)
                        consumer.commit(asynchronous=False)  # Offset manuell bestätigen
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode JSON: {e}")
                    except Exception as e:
                        logger.error(f"Failed to process message: {e}")
            finally:
                consumer.close()
                logger.info("Kafka Consumer stopped.")

        # Start the Consumer in a separate thread
        consumer_thread = threading.Thread(target=consume, daemon=True)
        consumer_thread.start()