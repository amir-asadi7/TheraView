import socketserver
from .web import Handler
from .core import get_network_ip, PORT
from .control import start_record_plus_preview

def run():
    with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), Handler) as httpd:
        ip = get_network_ip()
        if ip:
            print(f"Server reachable at http://{ip}:{PORT}")
        else:
            print("No network IP found. Device may not be connected.")

        start_record_plus_preview()
        httpd.serve_forever()
