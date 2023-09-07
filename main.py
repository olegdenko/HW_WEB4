
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread, Lock
import json
import logging
import mimetypes
import pathlib
import socket
import urllib.parse

lock = Lock()


BASE_DIR = pathlib.Path()


def socket_client():
    host = socket.gethostname()
    port = 5000
    client_socket = socket.socket()
    client_socket.connect((host, port))
    message = input('--> ')

    while message.lower().strip() != 'end':
        client_socket.send(message.encode())
        data = client_socket.recv(1024).decode()
        print(f'received message: {data}')
        message = input('--> ')

    client_socket.close()


def socket_server():
    host = socket.gethostname()
    port = 5000

    server_socket = socket.socket()
    server_socket.bind((host, port))
    server_socket.listen(2)
    conn, address = server_socket.accept()
    print(f'Connection from {address}')
    while True:
        data = conn.recv(100).decode()

        if not data:
            break
        print(f'received message: {data}')
        message = input('--> ')
        conn.send(message.encode())
    conn.close()


class HTTPHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        body = urllib.parse.unquote(body.decode())
        body.replace('=', '')
        payload = {str(datetime.now()): {key: value for key, value in [
            el.split('=') for el in body.split('&')]}}
        with open(BASE_DIR.joinpath('storage/data.json'), 'a', encoding='utf-8') as fd:
            json.dump(payload, fd, ensure_ascii=False)
        print(payload)

        self.send_response(302)
        self.send_header('Location', '/contact')
        self.end_headers()

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        logging.debug(f'{route}')
        match route.path:
            case "/":
                self.send_html('index.html')
            case "/message":
                self.send_html('message.html')
            case "/contact":
                self.send_html('contact.html')
            case _:
                file = BASE_DIR / route.path[1:]
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html('error.html', 404)

    def send_html(self, filename, status_code=200):           
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())

    def send_static(self, filename):
        self.send_response(200)
        mime_type, *rest = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-type', mime_type)
        else:
            self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())

    def render_tmplate(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()


def run(server=HTTPServer, handler=HTTPHandler):
    addres = ('', 3000)
    http_server = server(addres, handler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


def main():
    ss = Thread(target=socket_server)
    hs = Thread(target=run)
    ss.start()
    hs.start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, handlers=[
        logging.FileHandler("Web_app_log.txt")], format="%(asctime)s %(message)s")
    main()
