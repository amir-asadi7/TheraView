#! /home/pi/TheraView/venv/bin/python
import http.server
import socketserver
import subprocess
import threading
import time
import datetime
import signal
import json
import os
import socket

# ----------------------------
# Settings
# ----------------------------

CONFIG_FILE = "/home/pi/TheraView/config/theraview.conf"
    
def load_config(path):
    cfg = {}
    if not os.path.isfile(path):
        print("Config file not found. Using defaults.")
        return cfg
    with open(path, "r") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if "=" in s:
                k, v = s.split("=", 1)
                cfg[k.strip()] = v.strip()
    return cfg

CFG = load_config(CONFIG_FILE)

def cfg_str(key, default):
    return CFG.get(key, default)

def cfg_int(key, default):
    try:
        return int(CFG.get(key, default))
    except:
        return default

def cfg_bool(key, default):
    v = CFG.get(key, None)
    if v is None:
        return default
    return v.lower() in ["true", "1", "yes"]

# base settings first
DEVICE = cfg_str("DEVICE", "/dev/video0")
OUTPUT_DIR = cfg_str("OUTPUT_DIR", "recordings")

RECORD_WIDTH = cfg_int("RECORD_WIDTH", 1920)
RECORD_HEIGHT = cfg_int("RECORD_HEIGHT", 1080)

STREAM_WIDTH = cfg_int("STREAM_WIDTH", 640)
STREAM_HEIGHT = cfg_int("STREAM_HEIGHT", 480)

FRAMERATE = cfg_int("FRAMERATE", 30)
RECORD_BITRATE = cfg_int("RECORD_BITRATE", 8000)

ENABLE_SYSTEMD = cfg_bool("ENABLE_SYSTEMD", True)
ENABLE_HOTSPOT = cfg_bool("ENABLE_HOTSPOT", True)

# hostname checks
hostname = socket.gethostname().lower()

def is_TVA():
    return hostname.startswith("tva")

def is_TVB():
    return hostname.startswith("tvb")

# default placeholders
BASENAME_PREFIX = "TVX"
STREAM_TEXT = "TheraView X"
PORT = 5003

# apply config based on hostname
if is_TVA():
    BASENAME_PREFIX = cfg_str("BASENAME_PREFIX_A", "TVA")
    STREAM_TEXT = cfg_str("STREAM_TEXT_A", "TheraView A")
    PORT = cfg_int("PORT_A", 5001)

elif is_TVB():
    BASENAME_PREFIX = cfg_str("BASENAME_PREFIX_B", "TVB")
    STREAM_TEXT = cfg_str("STREAM_TEXT_B", "TheraView B")
    PORT = cfg_int("PORT_B", 5002)


def get_network_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except:
        return None
    finally:
        s.close()

def get_free_space_gb():
    st = os.statvfs("/")
    free_bytes = st.f_bavail * st.f_frsize
    return free_bytes / (1024 * 1024 * 1024)

# ----------------------------
# Globals
# ----------------------------
proc_lock = threading.Lock()
preview_proc = None          # preview-only pipeline
record_proc = None           # record+preview pipeline
active_record = True         # start in record+preview mode
current_filename = ""

# ----------------------------
# HTML
# ----------------------------

HTML_PAGE = b"""
<html>
  <body style="font-family: sans-serif; margin: 0; padding: 0; text-align: center;">

    <div style="margin-top: 20px;">
      <img src="/stream" width="640" height="480"
        style="object-fit: cover; border: 2px solid black; max-width: 95vw; height: auto;">
    </div>

    <br>

    <div id="rec_status" style="font-size: 28px; font-weight: bold; color: red;">
      Recording active
    </div>

    <div id="file_name" style="font-size: 22px; margin-top: 8px; color: black;">
    </div>

    <br>

    <button id="rec_btn"
      style="
        font-size: 34px;
        padding: 24px 50px;
        width: 80vw;
        max-width: 420px;
        border-radius: 14px;
      "
      onclick="toggleRecord()">
      Stop recording
    </button>

    <br><br>

    <button
      onclick="exitServer()"
      style="
        font-size: 30px;
        padding: 20px 45px;
        width: 75vw;
        max-width: 380px;
        border-radius: 14px;
        background-color: #333;
        color: white;
      "
    >
      Exit
    </button>

    <br><br>

    <div id="mem_status" style="font-size: 20px; margin-top: 8px; color: gray;">
    </div>

    <script>
      function updateMem() {
        fetch('/mem', { cache: 'no-store' })
          .then(r => r.json())
          .then(data => {
            document.getElementById("mem_status").innerText =
              data.free_gb + " GB free";
          });
      }

      function updateFilename() {
        fetch('/filename', { cache: 'no-store' })
          .then(r => r.json())
          .then(data => {
            if (data.name) {
              const simple = data.name.split('/').pop();
              document.getElementById("file_name").innerText = simple;
            } else {
              document.getElementById("file_name").innerText = "";
            }
          });
      }

      function toggleRecord() {
        fetch('/toggle_record', { cache: 'no-store' })
          .then(() => setTimeout(updateStatus, 250));
      }

      function updateStatus() {
        fetch('/status', { cache: 'no-store' })
          .then(r => r.json())
          .then(data => {
            const s = document.getElementById("rec_status");
            const b = document.getElementById("rec_btn");

            if (data.record_active) {
              s.innerText = "Recording active";
              s.style.color = "red";
              b.innerText = "Stop recording";
            } else {
              s.innerText = "Recording off";
              s.style.color = "gray";
              b.innerText = "Start recording";
            }
          });
      }

      function exitServer() {
        fetch('/exit', { cache: 'no-store' })
          .then(() => {
            alert("Server stopped");
          });
      }

      setInterval(updateStatus, 1500);
      setInterval(updateMem, 5000);
      setInterval(updateFilename, 2000);

      updateStatus();
      updateMem();
      updateFilename();
    </script>

  </body>
</html>
"""




# ----------------------------
# Pipelines
# ----------------------------

def preview_pipeline():
    # Preview-only branch, scaled with overlays, JPEG to multipart for the browser
    return [
        "gst-launch-1.0", "-e", "-q",
        "v4l2src", f"device={DEVICE}", "io-mode=dmabuf",
        "!", f"image/jpeg,width={RECORD_WIDTH},height={RECORD_HEIGHT},framerate={FRAMERATE}/1",
        "!", "jpegdec",
        "!", "videoscale",
        "!", f"video/x-raw,width={STREAM_WIDTH},height={STREAM_HEIGHT},framerate={FRAMERATE}/1",
        "!", "videoconvert",
        "!", "clockoverlay", "font-desc=Sans 16", "halignment=right", "valignment=bottom", "draw-outline=true","color=0xFFFFFFFF","outline-color=0xFF000000",
        "!", "textoverlay", f"text={STREAM_TEXT}", "valignment=top", "halignment=right", "font-desc=Sans, 16", "draw-outline=true","color=0xFFFFFFFF","outline-color=0xFF000000",
        "!", "jpegenc",
        "!", "multipartmux", "boundary=frame",
        "!", "filesink", "location=/dev/stdout",
    ]


def record_pipeline(filename):
    # Matches your bash script flow for the record branch and replaces the UDP branch with the browser preview
    return [
        "gst-launch-1.0", "-e", "-q",
        "v4l2src", f"device={DEVICE}", "io-mode=dmabuf",
        "!", f"image/jpeg,width={RECORD_WIDTH},height={RECORD_HEIGHT},framerate={FRAMERATE}/1",
        "!", "jpegdec",
        "!", "videoconvert",
        "!", "tee", "name=t",

        # Record branch
        "t.", "!", "queue",
        "!", "videoconvert",
        "!", "x264enc",
            f"bitrate={RECORD_BITRATE}",
            "speed-preset=ultrafast",
            "tune=zerolatency",
            f"key-int-max={FRAMERATE}",
        "!", "h264parse",
        "!", "mp4mux", "faststart=true",
        "!", "filesink", f"location={filename}",

        # Browser preview branch
        "t.", "!", "queue",
        "!", "videoscale",
        "!", f"video/x-raw,width={STREAM_WIDTH},height={STREAM_HEIGHT},framerate={FRAMERATE}/1",
        "!", "videoconvert",
        "!", "timeoverlay", "font-desc=Sans 16", "halignment=left", "valignment=bottom", "color=0xFFFF0000",
        "!", "clockoverlay", "font-desc=Sans 16", "halignment=right", "valignment=bottom", "draw-outline=true","color=0xFFFFFFFF","outline-color=0xFF000000",
        "!", "textoverlay", f"text={STREAM_TEXT}", "valignment=top", "halignment=right", "font-desc=Sans, 16", "draw-outline=true","color=0xFFFFFFFF","outline-color=0xFF000000", 
        "!", "jpegenc",
        "!", "multipartmux", "boundary=frame",
        "!", "filesink", "location=/dev/stdout",
    ]


# ----------------------------
# Process control
# ----------------------------

def start_preview_only():
    global preview_proc
    stop_pipelines()
    preview_proc = subprocess.Popen(
        preview_pipeline(),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=0,
    )


def start_record_plus_preview():
    global record_proc
    global current_filename
    stop_pipelines()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    current_filename = os.path.join(OUTPUT_DIR, f"{BASENAME_PREFIX}{ts}.mp4")
    filename = current_filename
    record_proc = subprocess.Popen(
        record_pipeline(filename),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=0,
    )


def stop_pipelines():
    global preview_proc, record_proc

    # Stop preview-only
    if preview_proc is not None:
        try:
            preview_proc.send_signal(signal.SIGINT)
            preview_proc.wait(timeout=5)
        except Exception:
            try:
                preview_proc.terminate()
                preview_proc.wait(timeout=3)
            except Exception:
                preview_proc.kill()
        preview_proc = None

    # Stop record+preview with time to finalize moov
    if record_proc is not None:
        try:
            record_proc.send_signal(signal.SIGINT)  # allows mp4mux to finish
            record_proc.wait(timeout=8)
        except Exception:
            try:
                record_proc.terminate()
                record_proc.wait(timeout=4)
            except Exception:
                record_proc.kill()
        record_proc = None


def current_pipe():
    if record_proc:
        return record_proc
    return preview_proc


# ----------------------------
# HTTP handler
# ----------------------------

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global active_record

        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(HTML_PAGE)
            return

        if self.path == "/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"record_active": active_record}).encode("utf8"))
            return

        if self.path == "/toggle_record":
            with proc_lock:
                if active_record:
                    active_record = False
                    start_preview_only()
                else:
                    active_record = True
                    start_record_plus_preview()
            self._simple(b"ok")
            return

        if self.path == "/stream":
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.end_headers()

            # Stream loop
            while True:
                with proc_lock:
                    proc = current_pipe()

                if proc is None:
                    time.sleep(0.05)
                    continue

                try:
                    chunk = proc.stdout.read(4096)
                except Exception:
                    time.sleep(0.02)
                    continue

                if not chunk:
                    time.sleep(0.02)
                    continue

                try:
                    self.wfile.write(chunk)
                except BrokenPipeError:
                    return
            # unreachable
            # return
            
        if self.path == "/exit":
            with proc_lock:
                stop_pipelines()
            self._simple(b"Exiting")
            # stop server after the response is flushed
            def stop_server():
                time.sleep(0.3)
                os._exit(0)
            threading.Thread(target=stop_server).start()
            return
        
        
        if self.path == "/mem":
            free = get_free_space_gb()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"free_gb": round(free, 2)}).encode("utf8"))
            return
        if self.path == "/filename":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"name": current_filename}).encode("utf8"))
            return

        self.send_error(404)

    def _simple(self, msg: bytes):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers
        self.wfile.write(msg)
        


# ----------------------------
# Main
# ----------------------------

with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), Handler) as httpd:
    ip = get_network_ip()
    if ip:
        print(f"Server reachable at http://{ip}:{PORT}")
    else:
        print("No network IP found. Device may not be connected.")
        
    # start in record+preview mode
    start_record_plus_preview()
    httpd.serve_forever()
