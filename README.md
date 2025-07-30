Needs a VPS hosting SSH Deamon + id_rsa file to connect to it 


## File: core/ssh_proxy.py
This module defines the SocksProxy class, which sets up a local SOCKS5 proxy server and forwards traffic through a secure SSH tunnel.

## Class: SocksProxy
This is a subclass of threading.Thread, so it runs in its own thread when started.


class SocksProxy(threading.Thread):
## __init__(self, config)
Initializes the proxy with user configuration (like SSH hostname, key path, and port).
'''
self.config: Dictionary with SSH connection info and local port.

self.running: Boolean to keep the proxy alive.

self.ssh_client: Instance of paramiko.SSHClient for the SSH connection.
'''

## run(self)
This is the main loop of the thread. It:

Tries to establish an SSH connection using credentials or key.

If it fails, waits 5 seconds and retries (like Psiphon’s reconnect loop).

On success, calls start_socks() to begin listening on 127.0.0.1:<port>.

'''
self.ssh_client.connect(...)  # Connect to remote SSH
self.start_socks()            # Start SOCKS5 proxy once connected
'''
## start_socks(self)
This sets up a SOCKS5 proxy listener on 127.0.0.1:<port>.

- Creates a socket and binds to the loopback address.

- Listens for connections.

- For each client, spawns a new thread and calls handle_connection().

client, addr = sock.accept()
threading.Thread(target=self.handle_connection, args=(client,), daemon=True).start()
'''
### handle_connection(self, client_socket)
This function handles one SOCKS5 client connection from start to finish.

Steps:

    1. SOCKS5 Handshake

    client_socket.recv(262)        # Get client’s handshake
    client_socket.sendall(b"\x05\x00")  # Accept (no authentication)
    2. Parse Client Request
    Client sends destination info:
        - IPv4
        - OR domain
        - AND a port
        ```
        addrtype = data[3]             # What address type is being used
        ```

# Get either IPv4 or domain string
3. Open SSH Forward Channel

remote = self.ssh_client.get_transport().open_channel(
    'direct-tcpip',
    (addr, port),                # Where to connect via SSH
    client_socket.getsockname()  # Where the request came from
)
This uses SSH’s ability to connect from the remote server to the requested target — like an outbound TCP jump.

4. SOCKS5 Success Response
Tells the client: “OK, we connected!”


client_socket.sendall(b"\x05\x00\x00\x01" + socket.inet_aton("127.0.0.1") + (port).to_bytes(2, 'big'))
5. Bi-directional Relay
Now it just shuttles data between client_socket and the SSH-forwarded remote socket.


r, _, _ = select.select([client_socket, remote], [], [])
if client_socket in r:
    data = client_socket.recv(4096)
    remote.send(data)
🧹 finally block
Closes both sockets to clean up after the client disconnects.

## start_tunnel(config)
This is the public function used in main.py. It simply initializes and starts the thread.


'''
def start_tunnel(config):
    proxy = SocksProxy(config)
    proxy.daemon = True
    proxy.start()

'''


## Function/Method	Purpose
__init__	Sets up the proxy and config
run	Connects via SSH and starts SOCKS listener
start_socks	Listens on local port and spawns client handlers
handle_connection	Handles SOCKS5 handshake, builds SSH tunnel, relays data
start_tunnel(config)	Entry point — starts the thread for the proxy