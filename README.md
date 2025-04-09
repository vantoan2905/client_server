
# Customer Data Import/Export Tool

## Overview
This project provides a Python-based tool to **Import** and **Export** customer data with support for **CSV** and **Excel** formats. It includes features to validate and preview data before saving it to the system. Export options also include **JSON** and **XML** formats.


##  Features

### 1. Import Customer Data

Allows users to upload `.csv` or `.xlsx` files to import customer records into the system.

####  Processing Steps:
1. **Validate file type** (`.csv`, `.xlsx` only).
2. **Select encoding** (e.g., UTF-8, UTF-16).
3. **Read data** using `pandas`.
4. **Data validation checks**:
   - Required columns: `id`, `name`, `email`, `phone`, `created_at`
   - Valid **email format** using `email-validator`
   - Valid **date format** (`ISO` or `dd/mm/yyyy`)
   - Catch **empty or malformed values**, with detailed error messages
5. **Preview** valid data or display errors.
6. **Confirm and save** data into the system (can be integrated with your backend).


### 2. Export Customer Data

Allows exporting current customer data into:

- **CSV** (`.csv`)
- **Excel** (`.xlsx`)
- **JSON** (`.json`)
- **XML** (`.xml`)

Supports encoding options (default is UTF-8).


## Technical Requirements

- **Language**: Python 3.x  
- **Suggested Libraries**:
  - `pandas`, `openpyxl`, `csv`, `json`, `xml.etree.ElementTree`
  - `email-validator` (for email checking)
  - `chardet` (for encoding detection)
- **Backend Integration**: Works standalone or can be integrated with Flask, Django, FastAPI, or pure Python-based APIs.
- **Logging**:
  - Logs every import/export operation: success/failure, number of records, and timestamps.



##  Setup Guide

```bash
python -m venv venv
source venv/bin/activate  

pip install -r requirements.txt
```


## Usage Example
### Clone Project
```bash 
git clone https://github.com/vantoan2905/client_server.git
cd client_server
```


### Run Server 
```bash

cd server
uvicorn server_file_receiver:app --reload

```

### Run Client
```bash
cd client 
python client_file_sender.py

```
## License

MIT License

 
