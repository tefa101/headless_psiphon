import socket
import threading
import select
import paramiko
from core.logger import log


class SocksProxy(threading.Thread):
    def __init__(self, config):
        threading.Thread.__init__(self)
        self.config = config
        self.ssh_client = None
        self.running = True

    def run(self):
        while self.running:
            try:
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh_client.connect(
                    hostname=self.config["host"],
                    port=self.config.get("port", 22),
                    username=self.config["username"],
                    key_filename=self.config["key_path"],
                    allow_agent=False,
                    look_for_keys=False,
                )
                log(f"SSH connected to {self.config['host']}", "success")
                self.start_socks()
            except Exception as e:
                log(f"Connection error: {e}", "error")
            log("Retrying in 5 seconds...", "warn")
            import time
            time.sleep(5)

    def start_socks(self):
        listen_port = self.config.get("local_port", 1080)
        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", listen_port))
        sock.listen(100)
        log(f"SOCKS5 Proxy listening on 127.0.0.1:{listen_port}", "success")

        while self.running:
            client, addr = sock.accept()
            threading.Thread(
                target=self.handle_connection,
                args=(client,),
                daemon=True
            ).start()

    def handle_connection(self, client_socket):
        try:
            # Handle SOCKS5 handshake
            client_socket.recv(262)
            client_socket.sendall(b"\x05\x00")  # No auth

            # Request details
            data = client_socket.recv(4)
            if len(data) < 4:
                return

            mode = data[1]
            addrtype = data[3]

            if addrtype == 1:  # IPv4
                addr = socket.inet_ntoa(client_socket.recv(4))
            elif addrtype == 3:  # Domain
                domain_len = client_socket.recv(1)[0]
                addr = client_socket.recv(domain_len).decode()
            else:
                return

            port = int.from_bytes(client_socket.recv(2), 'big')

            log(f"Forwarding to {addr}:{port}", "info")

            # Open SSH tunnel to target
            remote = self.ssh_client.get_transport().open_channel(
                'direct-tcpip',
                (addr, port),
                client_socket.getsockname()
            )

            if remote is None:
                log(f"Channel to {addr}:{port} failed.", "error")
                client_socket.close()
                return

            client_socket.sendall(b"\x05\x00\x00\x01" + socket.inet_aton("127.0.0.1") + (port).to_bytes(2, 'big'))

            # Relay traffic
            while True:
                r, _, _ = select.select([client_socket, remote], [], [])
                if client_socket in r:
                    data = client_socket.recv(4096)
                    if len(data) == 0:
                        break
                    remote.send(data)
                if remote in r:
                    data = remote.recv(4096)
                    if len(data) == 0:
                        break
                    client_socket.send(data)

        except Exception as e:
            log(f"SOCKS error: {e}", "error")
        finally:
            client_socket.close()
            try:
                remote.close()
            except:
                pass


def start_tunnel(config):
    proxy = SocksProxy(config)
    proxy.daemon = True
    proxy.start()
