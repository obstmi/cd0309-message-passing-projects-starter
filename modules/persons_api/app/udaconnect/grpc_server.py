from concurrent import futures
import grpc
from app.udaconnect.services import PersonService
from . import  person_pb2
from . import  person_pb2_grpc

class PersonServicer(person_pb2_grpc.PersonServiceServicer):
    def __init__(self, app):
        self.app = app

    def RetrieveAll(self, request, context):
        with self.app.app_context():
            # use existing PersonService.retrieve_all()-method
            persons = PersonService.retrieve_all()
            return person_pb2.PersonMessageList(
                persons=[
                    person_pb2.PersonMessage(
                        id=person.id,
                        first_name=person.first_name,
                        last_name=person.last_name,
                        company_name=person.company_name
                    )
                    for person in persons
                ]
            )
    
def serve(app):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    person_pb2_grpc.add_PersonServiceServicer_to_server(PersonServicer(app), server)
    server.add_insecure_port('[::]:5005')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    from app import create_app  # import the Flask-App-Factory
    flask_app = create_app()  # create the Flask-App
    serve(flask_app)  # pass the Flask-App to the gRPC-Server
