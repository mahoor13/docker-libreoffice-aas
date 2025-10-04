# Excel to CSV AAS (Asynchronous API Service)

This is a minimal Excel to CSV conversion service built using:

- [Python 3](https://www.python.org/) with [UNO](https://www.libreoffice.org/get-help/documentation/) bindings
- [LibreOffice](https://www.libreoffice.org/) running in headless mode
- [Supervisor](http://supervisord.org/) for process management

It accepts JSON-based POST requests to convert Excel files (xlsx, xls, xlsm) to CSV format.

## 📦 Docker Setup

This project is packaged in a lightweight Docker container built on top of [`linuxserver/libreoffice:25.2.5`](https://hub.docker.com/r/linuxserver/libreoffice) with supervisor managing both LibreOffice and the Python server processes.

### Build the Docker image

```bash
docker build -t excel-csv-aas .
```

### Run the container

```bash
docker run -p 8080:8080 excel-csv-aas
```

Once running, the service will be available at:
**`http://localhost:8080`**

## 📥 API Usage

### Endpoints

```
POST /
```

### Content-Type

```
application/json
```

### Request Body Format

```json
{
  "type": "xlsx",
  "content": "base64_encoded_excel_content"
}
```

- **`type`** – Excel file format (`xlsx`, `xls`, or `xlsm`)
- **`content`** – Base64 encoded Excel file content

### Example: Convert Excel to CSV

```bash
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"xlsx\",
    \"content\": \"$(cat ./input.xlsx|base64 -w0)\"
  }" --output output.csv
```

## 📄 Output

- Returns a CSV file directly in the response body.
- Response headers:
  ```
  Content-Type: text/csv
  Content-Length: <file_size>
  ```

## 🛠 Architecture

- **Supervisor** manages both LibreOffice and Python server processes
- **LibreOffice** runs in headless mode with socket connection on port 2002
- **Python server** connects to LibreOffice via UNO bindings and serves HTTP requests on port 8080
- **Automatic restart** - if either process crashes, supervisor restarts it
- **Separate logging** - each process has its own log files for debugging

## 🔧 Process Management

The service uses supervisor to manage two processes:

1. **LibreOffice process**: `libreoffice --accept="socket,host=localhost,port=2002;urp;" --headless`
2. **Python server**: `python3 server.py`

Both processes:

- Start automatically when the container starts
- Restart automatically if they crash
- Have separate log files in `/var/log/supervisor/`
- Run with proper priority (LibreOffice starts first)

## 📊 Logs

- LibreOffice logs: `/var/log/supervisor/libreoffice.out.log` and `/var/log/supervisor/libreoffice.err.log`
- Python server logs: `/var/log/supervisor/python-server.out.log` and `/var/log/supervisor/python-server.err.log`
- Supervisor logs: `/var/log/supervisor/supervisord.log`

## 📬 License

MIT – Use freely and modify as needed.
