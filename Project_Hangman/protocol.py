import json, struct

HEADER = struct.Struct('!I') # 4-byte unsigned integer in network byte order
MAX_MESSAGE_SIZE = 64 * 1024 # 64 KB

def send_message(sock, obj):
    data = json.dumps(obj, separators=(',', ':')).encode('utf-8')
    if len(data) > MAX_MESSAGE_SIZE:
        raise ValueError('Message too large.')
    sock.sendall(HEADER.pack(len(data)) + data) # length of message first, then the message itself

def _recv_bytes(sock, n):
    """Receive exactly n bytes from the socket."""

    buf = b'' # bytes
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk: raise ConnectionError('Connection closed.')
        buf += chunk
    return buf

def recv_message(sock):
    (size,) = HEADER.unpack(_recv_bytes(sock, HEADER.size))
    if size > MAX_MESSAGE_SIZE: 
        raise ValueError('Message too large.')
    return json.loads(_recv_bytes(sock, size).decode('utf-8'))