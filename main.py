from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread, Lock
import threading
import json
import logging
import mimetypes
import pathlib
import socket
import signal
import urllib.parse


lock = Lock()
stop_event = threading.Event()


BASE_DIR = pathlib.Path()
HOST = socket.gethostname()
HOST_OUT = "0.0.0.0"
HTTP_SRV_PORT = 3000
SOCKET_SRV_PORT = 5000
STATUS_OK = 200
STATUS_ER = 404
STATUS_MV = 302
BUFER1 = 100
BUFER2 = 1024

env = Environment(loader=FileSystemLoader("templates"))
stop_threads = False


def run_socket_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST, SOCKET_SRV_PORT))
    try:
        while not stop_event.is_set():
            msg, address = server_socket.recvfrom(BUFER2)
            logging.info(f"Connection from {address}")
            if not msg:
                break
            save_data(msg)
        logging.info(f"received message: {msg}")
    except KeyboardInterrupt:
        logging.info("Socket server stopped")
    finally:
        server_socket.close()


def send_data_to_socket(body):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(body, (HOST, SOCKET_SRV_PORT))
    client_socket.close()


class HTTPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global stop_threads
        content_length = int(self.headers["Content-Length"])
        body = self.rfile.read(content_length)

        body_str = body.decode()

        if "killall" in body_str:
            stop_event.set()
            print("killall")
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
    addres = (HOST_OUT, HTTP_SRV_PORT)
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


def main():
    ss = Thread(target=run_socket_server)
    ss.start()
    hs = Thread(target=run_http_server)
    hs.start()

    stop_event.wait()

    ss.join()
    hs.join()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[logging.FileHandler("Web_app_log.txt")],
        format="%(asctime)s %(threadName)s %(message)s",
    )
    STORAGE_DIR = pathlib.Path().joinpath("storage")
    FILE_STORAGE = STORAGE_DIR / "data.json"
    if not FILE_STORAGE.exists():
        with open(FILE_STORAGE, "w", encoding="utf-8") as fd:
            json.dump({}, fd, ensure_ascii=False)

    main()
