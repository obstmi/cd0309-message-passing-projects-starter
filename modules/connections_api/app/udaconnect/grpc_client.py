import grpc
from . import person_pb2
from . import person_pb2_grpc

class PersonServiceClient:
    def __init__(self, host='udaconnect-persons-api', port=5005):
        self.channel = grpc.insecure_channel(f'{host}:{port}')
        self.stub = person_pb2_grpc.PersonServiceStub(self.channel)

    def retrieve_all(self):
        response = self.stub.RetrieveAll(person_pb2.Empty())
        return response.persons

    def close(self):
        self.channel.close()
