import uno
import sys
import json
import base64
import os
import random
import string
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse


def random_filename(ext: str) -> str:
    """Generate a random filename with given extension in current directory."""
    rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    return os.path.join(os.getcwd(), f"./tmp/{rand}.{ext}")

def ensure_url(path: str) -> str:
    """Convert a filesystem path to a UNO file URL if needed."""
    return path if path.startswith("file://") else uno.systemPathToFileUrl(path)

def convert_to_csv(input_path: str, output_path: str):
    """Convert Excel file to CSV using LibreOffice."""
    input_url = ensure_url(input_path)
    output_url = ensure_url(output_path)

    # Connect to running LibreOffice instance
    local_ctx = uno.getComponentContext()
    resolver = local_ctx.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local_ctx
    )
    ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
    desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)

    # Load spreadsheet
    document = desktop.loadComponentFromURL(input_url, "_blank", 0, [])

    # Detect the active sheet automatically
    controller = document.getCurrentController()
    sheet = controller.getActiveSheet()
    controller.setActiveSheet(sheet)

    # Prepare export properties
    props = (
        uno.createUnoStruct("com.sun.star.beans.PropertyValue"),
        uno.createUnoStruct("com.sun.star.beans.PropertyValue"),
    )
    props[0].Name = "FilterName"
    props[0].Value = "Text - txt - csv (StarCalc)"
    props[1].Name = "FilterOptions"
    props[1].Value = "44,34,76,1"  # Field sep=,  text sep=", encoding=UTF8, first line

    # Save to CSV
    document.storeToURL(output_url, props)
    document.close(True)

class ExcelToCSVHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)

            # Parse JSON
            data = json.loads(body.decode('utf-8'))
            file_type = data.get('type', '').lower()
            content_b64 = data.get('content', '')

            # Validate file type
            if file_type not in ['xls', 'xlsx', 'xlsm']:
                self.send_error(400, f"Invalid file type: {file_type}. Must be xls, xlsx, or xlsm")
                return

            # Decode base64 content
            file_content = base64.b64decode(content_b64)

            input_path = random_filename(file_type)
            output_path = random_filename("csv")

            with open(input_path, 'wb') as f:
                f.write(file_content)

            try:
                # Convert to CSV
                print(f"convert {input_path}:{output_path}")
                convert_to_csv(input_path, output_path)

                # Read CSV content
                with open(output_path, 'r', encoding='utf-8') as f:
                    csv_content = f.read()

                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'text/csv')
                self.send_header('Content-Length', str(len(csv_content.encode('utf-8'))))
                self.end_headers()
                self.wfile.write(csv_content.encode('utf-8'))

            finally:
                # Clean up temporary files
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(output_path):
                    os.remove(output_path)

        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
        except KeyError as e:
            self.send_error(400, f"Missing required field: {e}")
        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")

    def log_message(self, format, *args):
        """Log requests to stdout."""
        sys.stdout.write(f"{self.address_string()} - [{self.log_date_time_string()}] {format % args}\n")

def main():
    host = '0.0.0.0'
    port = 8080

    server = HTTPServer((host, port), ExcelToCSVHandler)
    print(f"🚀 Excel to CSV service running on http://{host}:{port}")
    print(f"📝 Send POST requests with JSON body: {{\"type\":\"xlsx\",\"content\":\"<base64>\"}}")
    print(f"✅ Returns: text/csv")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        server.shutdown()

if __name__ == "__main__":
    main()