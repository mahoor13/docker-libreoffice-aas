# Excel to CSV AAS (Asynchronous API Service)

This is a minimal Excel to CSV conversion service built using:

- [FrankenPHP](https://github.com/dunglas/frankenphp)
- [LibreOffice](https://www.libreoffice.org/)
- PHP (no frameworks or dependencies)

It accepts JSON-based POST requests to convert Excel files (xlsx, xls, xlsm) to CSV format.

## 📦 Docker Setup

This project is packaged in a lightweight Docker container built on top of [`linuxserver/libreoffice:25.2.5`](https://hub.docker.com/r/linuxserver/libreoffice).

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
  "excelData": "base64_encoded_excel_content",
  "excel": "/path/to/excel/file.xlsx", // optional alternative to excelData
  "params": {
    "format": "xlsx" // xlsx, xls, or xlsm
  },
  "output": "converted_file.csv", // optional: save to output directory
  "debug": true // optional: creates doc.sh with the command used
}
```

- **`excelData`** – (optional) Base64 encoded Excel file content.
- **`excel`** – (optional) File path to Excel file on server (alternative to excelData).
- **`params`** – Conversion options:
  - `format`: Excel file format (`xlsx`, `xls`, or `xlsm`)
- **`output`** – (optional) Filename to save in output directory.
- **`debug`** – (optional) Creates a `doc.sh` file with the LibreOffice command used.

**Note:** Either `excelData` or `excel` must be provided, but not both.

### Example: Convert Excel to CSV from base64 data

```bash
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "excelData": "UEsDBBQAAAAIAA==",
    "params": {
      "format": "xlsx"
    },
    "output": "converted_file.csv"
  }' --output output.csv
```

### Example: Convert Excel file from server path

```bash
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "excel": "/app/sample.xlsx",
    "output": "converted_file.csv"
  }' --output output.csv
```

## 📄 Output

- Returns a CSV file directly in the response body.
- Response headers sample:
  ```
  Content-Type: text/csv
  Content-Disposition: inline; filename="output.csv"
  ```

## 🛠 Notes

- Only one of `excelData` or `excel` should be provided.
- FrankenPHP runs PHP as a fast, async worker – perfect for containerized services.
- Supports Excel formats: xlsx, xls, xlsm
- LibreOffice runs in headless mode for server conversion

## 🤔 Why FrankenPHP Instead of Python?

This service is built with **FrankenPHP** instead of a Python-based stack to take advantage of its **lightweight, high-concurrency architecture**. FrankenPHP runs as a blazing-fast, production-grade PHP server with native support for async workers and HTTP/1.1/2.0. Unlike typical Python solutions (e.g. Flask + Gunicorn), FrankenPHP offers **built-in concurrency without needing additional layers or process managers**, resulting in faster response times and lower overhead. Thanks to its minimal runtime and efficient memory footprint, the final Docker image is **significantly smaller** than equivalent Python-based containers, making it ideal for microservices, cold starts, and edge deployments.

## 📬 License

MIT – Use freely and modify as needed.
