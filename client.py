import sys
from threading import Thread, Event
import rpyc
import zmq
from constPS import *  # -
import time

# menu option constants
DIRECT = 1
GROUP = 2
EXIT = 3 


options = {
    DIRECT  : "send direct message",
    GROUP   : "send group message",
    EXIT    : "exit"
}


def print_options() -> None:
    for key in options.keys():
        print(key, options[key])


def group_msg_format(groupname: str, username: str, message:  str) -> str:
    return f"{groupname} {username}:{message}"


def receive_group_messages(groupname: str, username: str, stop_event: Event) -> None:
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect(f"tcp://{SERVER}:{SUB}")
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

    while True:
        message = subscriber.recv_string()
        print(message)
        if stop_event.is_set():
            break
        if not message.startswith(f"{groupname} {username}:"):
            print(message)
    
    subscriber.close()
    context.term()


def send_group() -> None:
    username = input("what is your username:")
    groupname = input("what is the group name?")
    
    stop_event = Event()
    receive_t = Thread(target= lambda: receive_group_messages(groupname, username, stop_event))
    receive_t.start()

    context = zmq.Context()
    publisher = context.socket(zmq.PUB)
    publisher.connect(f"tcp://{SERVER}:{PUB}")

    while True: 
        message = input("Enter the message:")
        if message.lower() == "exit":
            stop_event.set()
            publisher.send_string(group_msg_format(groupname, username, "left the group"))
            print("exiting...")
            break

        payload = group_msg_format(groupname, username, message)
        publisher.send_string(payload)
    receive_t.join()
    publisher.close()
    context.term()
    print("you exit the group.")
    

def send_direct() -> None:
    conn = rpyc.connect(SERVER, DIRECT)

    user_name = input("Please enter your name: ")
    destination = input("enter the destination name: ")

    try:
        while True:
            input_var = input()
            if input_var == "exit":
                conn.root.exit(user_name)
                break
            input_var = user_name + ":" + input_var
            conn.root.set_remote_print(print, user_name)
            conn.root.send_message(input_var, destination)
    except Exception as errtxt:
        print("error")


def main(args):
    while True:
        print_options()
        response = int(input(">"))
        if response not in options.keys(): 
            print("invalid answer")
            continue

        if response == EXIT: 
            print("goodbye :)")
            break

        if response == GROUP:
            send_group()
        
        if response == DIRECT:
            send_direct()


if __name__ == "__main__":
    main(sys.argv[1:])