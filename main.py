from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import subprocess
import os
import json
import time

PORT = 8080
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

class SpotDLServer(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/sptdl":
            query = parse_qs(parsed.query)
            url = query.get("url", [None])[0]

            if not url:
                self.respond_json({"error": "Missing 'url' parameter"})
                return

            timestamp = str(int(time.time()))
            print(f"[REQUEST] Spotify URL: {url}")

            # Capture files before download
            before_files = set(os.listdir(DOWNLOAD_DIR))

            try:
                subprocess.run(
                    ["spotdl", url, "--output", DOWNLOAD_DIR + "/"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

                # Find new file
                after_files = set(os.listdir(DOWNLOAD_DIR))
                new_files = list(after_files - before_files)
                if not new_files:
                    raise Exception("No file downloaded")

                original_file = new_files[0]
                original_path = os.path.join(DOWNLOAD_DIR, original_file)
                renamed_path = os.path.join(DOWNLOAD_DIR, f"{timestamp}.mp3")

                os.rename(original_path, renamed_path)

                # Extract real song title (remove .mp3 extension)
                real_title = os.path.splitext(original_file)[0]

                host = self.headers.get("Host")
                download_url = f"http://{host}/{renamed_path}"

                print(f"[SUCCESS] Downloaded: {real_title}")
                print(f"[SAVED AS] {timestamp}.mp3")

                self.respond_json({
                    "title": real_title,
                    "download_link": download_url
                })

            except Exception as e:
                print(f"[ERROR] {str(e)}")
                self.respond_json({"error": str(e)})

        elif self.path.startswith(f"/{DOWNLOAD_DIR}/"):
            file_path = self.path.lstrip("/")
            if os.path.isfile(file_path):
                with open(file_path, "rb") as f:
                    self.send_response(200)
                    self.send_header("Content-Type", "audio/mpeg")
                    self.end_headers()
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "File not found.")
        else:
            self.send_error(404, "Invalid endpoint.")

    def respond_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

def run_server():
    print(f"[SERVER] SpotDL server running at http://0.0.0.0:{PORT}")
    HTTPServer(("0.0.0.0", PORT), SpotDLServer).serve_forever()

if __name__ == "__main__":
    run_server() 