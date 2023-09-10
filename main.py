from jinja2 import Environment, FileSystemLoader
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
STATUS_OK = 200
STATUS_ER = 404
STATUS_MV = 302
BUFER1 = 100
BUFER2 = 1024

env = Environment(loader=FileSystemLoader("templates"))


def run_socket_server():
    host = socket.gethostname()
    port = 5000

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    # server_socket.listen()
    # conn, address = server_socket.accept()
    # logging.info(f"Connection from {address}")
    try:
        while True:
            msg, address = server_socket.recvfrom(BUFER2)
            logging.info(f"Connection from {address}")
            if not msg:
                break
            # if msg == 'kill all':
            #     server_stop()

            save_data(msg)
        logging.info(f"received message: {msg}")
    except KeyboardInterrupt:
        logging.info("Socket server stopped")
    finally:
        server_socket.close()


def send_data_to_socket(body):
    host = socket.gethostname()
    port = 5000
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # client_socket.connect((host, port))
    client_socket.sendto(body, (host, port))
    client_socket.close()


class HTTPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        body = self.rfile.read(content_length)

        send_data_to_socket(body)
        self.send_response(STATUS_MV)
        self.send_header("Location", "/contact")
        self.end_headers()

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        logging.debug(f"{route}")
        match route.path:
            case "/":
                self.send_html("index.html")
            case "/message":
                self.send_html("message.html")
            case "/contact":
                self.send_html("contact.html")
            case "/blog":
                self.send_html("blog.html")
            case _:
                file = BASE_DIR / route.path[1:]
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html("error.html", STATUS_ER)

    def send_html(self, filename, status_code=STATUS_OK):
        self.send_response(status_code)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as f:
            self.wfile.write(f.read())

    def render_template(self, filename, status_code=STATUS_OK):
        self.send_response(status_code)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open("blog.json", "r", encoding="utf-8") as fd:
            r = json.load(fd)
        template = env.get_template(filename)
        print(template)
        html = template.render(blogs=r)
        self.wfile.write(html.encode())

    def send_static(self, filename):
        self.send_response(STATUS_OK)
        mime_type, *rest = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header("Content-type", mime_type)
        else:
            self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as f:
            self.wfile.write(f.read())


def run_http_server(server=HTTPServer, handler=HTTPHandler):
    addres = ("", 3000)
    http_server = server(addres, handler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


def save_data(data):
    body = urllib.parse.unquote_plus(data.decode())
    try:
        with open(BASE_DIR.joinpath("storage/data.json"), "r", encoding="utf-8") as fd:
            data = json.load(fd)
    except FileNotFoundError:
        data = {}
    payload_data = {
        key: value for key, value in [el.split("=") for el in body.split("&")]
    }

    timestamp = str(datetime.now())
    data[timestamp] = payload_data

    with open(BASE_DIR.joinpath("storage/data.json"), "w", encoding="utf-8") as fd:
        json.dump(data, fd, ensure_ascii=False, indent=4)

    # try:
    #     payload = {
    #         str(datetime.now()): {
    #             key: value for key, value in [el.split("=") for el in body.split("&")]
    #         }
    #     }
    #     with open(BASE_DIR.joinpath("storage/data.json"), "w", encoding="utf-8") as fd:
    #         json.dump(payload, fd, ensure_ascii=False)
    # except ValueError as err:
    #     logging.error(f"Filed parse data: {body} with error {err}")
    # except OSError as err:
    #     logging.error(f"Filed write data: {body} with error {err}")


def main():
    ss = Thread(target=run_socket_server)
    ss.start()
    hs = Thread(target=run_http_server)
    hs.start()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[logging.FileHandler("Web_app_log.txt")],
        format="%(asctime)s %(threadName)s %(message)s",
    )
    main()
