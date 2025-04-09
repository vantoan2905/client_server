import requests
import json
import os
import io
import pandas as pd
import xml.etree.ElementTree as ET
import asyncio
import websockets
import base64
import asyncio
import questionary
import chardet


BASE_URL = "http://localhost:8000"



WS_URL = "ws://localhost:8000/ws/import"

async def call_import_ws(admin_name, path, encoding='utf-8'):
    print(f"[WebSocket] Calling /ws/import with admin_name: {admin_name}, path: {path}, encoding: {encoding}")

    if not os.path.exists(path):
        print(f"File '{path}' does not exist.")
        return

    try:
        file_name = os.path.basename(path)

        if path.endswith('.csv'):
            with open(path, 'rb') as f:
                result = chardet.detect(f.read(1000))
            df = pd.read_csv(path, encoding=result['encoding'])
            print("Read file csv...\n")
        elif path.endswith('.xlsx'):
            df = pd.read_excel(path, engine='openpyxl')
            print("Read file xlsx...\n")
        else:
            print("Unsupported file type.")
            return

        payload = {
            "adminname": admin_name,
            "filename": file_name,
            "encoding": encoding,
            "data": df.to_dict(orient='records')
        }

        async with websockets.connect(WS_URL) as websocket:
            await websocket.send(json.dumps(payload))
            while True:
                response = await websocket.recv()
                print("[WebSocket] Server:", response)
                if "Do you want to save" in response:
                    await websocket.send(input("Input 'yes' or 'no': ").strip().lower())
                else:
                    break

    except Exception as e:
        print(f"Error during WebSocket import: {e}")



def call_export(admin_name, dir_path, file_name, mode_export, encoding='utf-8', mode_file='csv'):
    print(f"Calling /export with admin_name: {admin_name}, file name {file_name}, encoding: {encoding}")
    url = f"{BASE_URL}/export"

    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
        print(f"path is not exist, create new path: {dir_path}")

    response = requests.get(url, params={
        "adminname": admin_name,
        "filename": file_name,
        "mode_export": mode_export,
        "encoding": encoding,
        "mode_file": mode_file
    })

    header = response.headers.get("Content-Disposition")
    name_save_name = header[9:] if header else file_name
    full_path = os.path.join(dir_path, name_save_name)

    temp_file = io.BytesIO(response.content)
    # xml process
    if mode_file == 'xml':
        if encoding.startswith('utf-'):
            text = temp_file.getvalue().decode(encoding) 
            with open(full_path, "w", encoding=encoding) as f:
                f.write(text)
            print(f"Saved to {full_path} with encoding {encoding}")
        elif encoding == "base64":
            encoded = base64.b64encode(temp_file.getvalue()).decode(encoding)
            with open(full_path, "w", encoding=encoding) as f:
                f.write(encoded)
            print(f"Saved base64-encoded file to {full_path}")
    # -----------------------------------------------------------------------------
    # json process
    elif mode_file == "json":
        text = temp_file.getvalue()

        with open(full_path, "wb") as f:
            f.write(text)

        print(f"Saved to {full_path}")
    # -----------------------------------------------------------------------------
    # csv process
    elif mode_file == "csv":
        text = temp_file.getvalue().decode(encoding)
        with open(full_path, "w", encoding=encoding) as f:
            f.write(text)
        print(f"Saved to {full_path} with encoding {encoding}")
    # -----------------------------------------------------------------------------
    # xlsx process
    elif mode_file == "xlsx":
        with open(full_path, "wb") as f:
            f.write(temp_file.getvalue())
        print(f"Saved to {full_path}")
        
        
    

    else:
        print("Unsupported encoding.")
        return
      
    
 



if __name__ == "__main__":
    while True:
        command = questionary.select(
            "Choose a command:",
            choices=["Import", "Export", "Quit"]
        ).ask().lower()

        if command == "import":
            while True:
                admin_name = questionary.text("Admin name:").ask()
                file_path = questionary.path("Path to import file:").ask()
                encoding = questionary.text("Encoding (default utf-8) supported for type csv:", default="utf-8").ask()
                # ----------------------------------------------------------------------
                # check type file
                # ----------------------------------------------------------------------
                if file_path.split('.')[-1] in ['csv', 'xlsx']:
                    break
                elif file_path.split('.')[-1] not in ['csv', 'xlsx']:
                    print("Unsupported file type.")
                if admin_name == '' or file_path == '' or encoding == '':
                    print("Admin name, path and encoding are required.")
                else:
                    break

            asyncio.run(call_import_ws(admin_name, file_path, encoding))

        elif command == "export":
            
            while True:
                admin_name = questionary.text("Admin name:").ask()
                save_path = questionary.path("Save directory:").ask()
                file_name = questionary.text("File name:").ask()
                if admin_name == '' or save_path == '' or file_name == '':
                    print("Admin name, save path and file name are required.")
                else:
                    break
                
            while True:
                mode_export = questionary.text("Export mode all or one (default all):", default="all").ask()
                if mode_export in ['all', 'one']:
                    break
            while True:
                mode_file = questionary.text("File mode export csv, xlsx, json or xml (default csv):", default="csv").ask()
                if mode_file in ['csv', 'xlsx', 'json', 'xml']:
                    break
               
            encoding = questionary.text("Encoding (default utf-8) support csv and xml:", default="utf-8").ask()
            call_export(admin_name=admin_name, dir_path=save_path, file_name=file_name,
                        mode_export=mode_export, encoding=encoding, mode_file=mode_file)

        elif command == "quit":
            print("Goodbye!")
            break
