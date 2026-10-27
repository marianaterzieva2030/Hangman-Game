import argparse
import logging
import os
import socket
import sys
import threading

from db import session
from handlers import dispatch, new_state
from protocol import send_message, recv_message

log = logging.getLogger('hangman.server')

DEFAULT_HOST = os.environ.get('HANGMAN_HOST', '127.0.0.1')
DEFAULT_PORT = int(os.environ.get('HANGMAN_PORT', 9999))
CLIENT_IDLE_TIMEOUT = 600 # seconds without any request


def make_server_socket(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if os.name != 'nt': # on Windows SO_REUSEADDR has different semantics and is not needed
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen()
    return sock

def handle_client(conn, addr):
    log.info(f'Connected: {addr}')
    conn.settimeout(CLIENT_IDLE_TIMEOUT)
    state = new_state()
    try:
        while True:
            try:
                request = recv_message(conn)
            except OSError: # closed, reset, or idle timeout
                break
            except ValueError as e: # bad framing, bad JSON, bad utf-8
                log.warning(f'Bad message from {addr}: {e}')
                break

            reply = dispatch(request, state) # never raises an exception
            try:
                send_message(conn, reply)
            except (OSError, ValueError):
                break
    finally:
        session.remove()
        conn.close()
        log.info(f'Disconnected: {addr}')

def serve(server_sock, stop_event=None):
    server_sock.settimeout(1.0)
    while stop_event is None or not stop_event.is_set():
        try:
            conn, addr = server_sock.accept()
        except socket.timeout:
            continue
        except OSError: # listening socket was closed
            break
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default=DEFAULT_HOST)
    parser.add_argument('--port', type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    try:
        server_sock = make_server_socket(args.host, args.port)
    except OSError as e:
        log.error(f'Cannot start server on {args.host}:{args.port}: {e}')
        sys.exit(1)

    log.info(f'Server started on {args.host}:{args.port}')
    try:
        serve(server_sock)
    except KeyboardInterrupt:
        log.info('Shutting down.')
    finally:
        server_sock.close()


if __name__ == '__main__':
    main()