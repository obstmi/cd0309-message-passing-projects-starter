import os
from app.udaconnect.services import LocationService
from app import create_app

app = create_app(os.getenv("FLASK_ENV") or "test")

LocationService.start_kafka_consumer()

if __name__ == "__main__":
    app.run(debug=True)
