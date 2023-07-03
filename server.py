import rpyc
import zmq
from constPS import *
from rpyc.utils.server import ThreadedServer


def broker():
    context = zmq.Context()
    frontend = context.socket(zmq.XSUB)
    frontend.bind(f"tcp://*:{SUB}")

    backend = context.socket(zmq.XPUB)
    backend.bind(f"tcp://*:{PUB}")

    zmq.proxy(frontend, backend)

    frontend.close()
    backend.close()
    context.term()


class MyService(rpyc.Service):

    def on_connect(self, conn):
        self.users = {} 
        self.conversations = {}

    def exposed_exit(self, username):
        conversations = self.conversations.get(username, None)
        if not conversations: 
            raise Exception("user not register")

        for user in conversations: 
            func = self.users[user]
            func(f"{username} left :(")
        
        self.conversations.pop(username)
        self.users.pop(username)


    def exposed_send_message(self, message, destination, username):
        # only send to the destination
        user_f = self.users.get(username, None)
        if not user_f:
            raise Exception("user not register")

        dest_f = self.users.get(destination, None)
        if not dest_f:
            user_f("error: user didn't join!")
            return

        dest_f(message)
        self.add_conversation(destination, username)
        self.add_conversation(username, destination)


    def exposed_set_remote_print(self, fn, name):
        self.users[name] = fn


    def add_convesation(self, username, destination):
        convs_user = self.conversations.get(username)
        if not convs_user:
            convs_user = [destination]
            return
        
        if destination not in convs_user:
            convs_user.append(destination)



if __name__ == "__main__":
    broker()

    t = ThreadedServer(MyService, port=18888)
    t.start()


