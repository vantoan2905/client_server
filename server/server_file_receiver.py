import os
import csv
import json
import logging
import xml.etree.ElementTree as ET
import datetime
from io import StringIO, BytesIO

import chardet
import pandas as pd
from dateutil import parser as date_parser  
from email_validator import validate_email, EmailNotValidError
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, JSONResponse
from dicttoxml import dicttoxml

from data_process import Database  
from schema import ImportRequest, ExportRequest

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db_global = Database("sever_file.db")
db_global.create_table()


# -----------------------------------------------------------------------------------------
# check data
# -----------------------------------------------------------------------------------------
def check_data(df: pd.DataFrame):
    required_columns = ["id", "name", "email", "phone", "created_at"]
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        return [{"row": "all", "messages": [f"Missing column '{col}'" for col in missing_cols]}]

    errors = []
    for idx, row in df.iterrows():
        row_errors = []
        for field in ["id", "name", "email", "created_at"]:
            if pd.isna(row[field]) or not str(row[field]).strip():
                row_errors.append(f"Missing data in '{field}'")
        # Validate email
        try:
            validate_email(row['email'])
        except EmailNotValidError:
            row_errors.append(f"Invalid email format: {row['email']}")
        # Validate date (expected dd/mm/YYYY)
        try:
            datetime.datetime.strptime(str(row['created_at']), "%d/%m/%Y")
        except ValueError:
            row_errors.append(f"Invalid date format (expected dd/mm/YYYY): {row['created_at']}")
        if row_errors:
            errors.append({"row": idx + 1, "messages": row_errors})
    return errors

# -----------------------------------------------------------------------------------------
# WebSocket Import Endpoint
# -----------------------------------------------------------------------------------------
@app.websocket("/ws/import")
async def websocket_import(websocket: WebSocket):
    await websocket.accept()
    try:
        payload = await websocket.receive_json()
        db = Database("sever_file.db")
        db.create_table()

        adminname = payload.get("adminname")
        filename = payload.get("filename")
        encoding = payload.get("encoding", "utf-8")
        records = payload.get("data")

        logger.info(f"[IMPORT RECEIVED] Admin: {adminname}, File: {filename}, Encoding: {encoding}")
        logger.info(f"Total records: {len(records) if records else 0}")

        if not records:
            await websocket.send_json({"error": "No data provided"})
            return

        if filename.split('.')[-1] not in ['csv', 'xlsx']:
            await websocket.send_json({"error": "Unsupported file type"})
            return

        df = pd.DataFrame(records)
        errors = check_data(df)
        if errors:
            db.insert_log(adminname, filename, "import", "failed", len(records))
            await websocket.send_json({"error": errors})
            return

        await websocket.send_text("Data is valid. Do you want to save file to database?")
        client_response = (await websocket.receive_text()).strip().lower()

        if client_response == "yes":
            db.insert_data(adminname, filename)
            for record in records:
                try:
                    db.insert_user(record['name'], record['email'], record['phone'], record['created_at'], filename)
                except Exception as e:
                    logger.error(f"Error inserting record {record}: {e}")
                    await websocket.send_json({"error": f"Error inserting record: {e}"})
                    return
            db.insert_log(adminname, filename, "import", "success", len(records))
            await websocket.send_json({"message": "Import successful", "record_count": len(records)})
        elif client_response == "no":
            db.insert_log(adminname, filename, "import", "failed", len(records))
            await websocket.send_text("Client chose not to save the file.")
        else:
            await websocket.send_text("Invalid response. Expected 'yes' or 'no'.")

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        await websocket.send_json({"error": str(e)})

# -----------------------------------------------------------------------------------------
# Export File Endpoint
# -----------------------------------------------------------------------------------------
@app.get("/export")
async def export_file(adminname: str, filename: str, mode_export: str, encoding: str = 'utf-8', mode_file: str = 'csv'):
    if not adminname or not filename:
        raise HTTPException(status_code=400, detail="Admin name and filename are required")
    if mode_file not in ['csv', 'xlsx', 'json', 'xml']:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    if mode_export not in ['all', 'one']:
        raise HTTPException(status_code=400, detail="Unsupported mode export")

    db = Database("sever_file.db")
    try:
        users = []
        if mode_export == 'all':
            all_files = db.get_file_by_adminname(adminname)
            for file in all_files:
                users.extend(db.get_user_by_file(file[2]))
        else:  # mode_export == 'one'
            if not db.get_file_by_adminname(adminname):
                raise HTTPException(status_code=404, detail="No data found for the given admin name")
            users = db.get_user_by_file(filename)

        if not users:
            raise HTTPException(status_code=404, detail="No data found")

        json_data = [{
            "username": u[1],
            "email": u[2],
            "phone": u[3],
            "created_at": u[4],
            "filename": u[5]
        } for u in users]
        export_name = f"{adminname}_{'all' if mode_export == 'all' else filename.rsplit('.', 1)[0]}"

        if mode_file == 'csv':
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=json_data[0].keys())
            writer.writeheader()
            writer.writerows(json_data)
            content = output.getvalue().encode(encoding)
            response = Response(content=content, media_type="text/csv")
        elif mode_file == 'xlsx':
            df = pd.DataFrame(json_data)
            output = BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)
            content = output.getvalue()
            response = Response(content=content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        elif mode_file == 'json':
            json_string = json.dumps(json_data, ensure_ascii=False)
            content = json_string.encode(encoding)
            response = Response(content=content, media_type="application/json")
        elif mode_file == 'xml':
            root = ET.Element("users")
            for user in json_data:
                user_element = ET.SubElement(root, "user")
                for key, value in user.items():
                    child = ET.SubElement(user_element, key)
                    child.text = str(value)
            content = ET.tostring(root, encoding=encoding)
            response = Response(content=content, media_type="application/xml")

        response.headers["Content-Disposition"] = f"filename={export_name}.{mode_file}"
        db.insert_log(adminname, filename, "export", "success", len(json_data))
        return response

    except Exception as e:
        db.insert_log(adminname, filename, "export", "failed", 0)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
