import sqlite3
import datetime

class Database:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adminname TEXT,
            filename TEXT
        )''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT,
            phone TEXT,
            created_at TEXT,
            filename TEXT
        )''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adminname TEXT,
            filename TEXT,
            action TEXT,
            status TEXT,
            number_of_records INTEGER,
            created_at TEXT
        )''')  

        self.conn.commit()

    def insert_data(self, adminname, filename):
        if not filename.endswith(('.csv', '.json', '.xml', '.xlsx')):
            raise ValueError("Filename must be a .csv, .json, .xml or .xlsx file")

        self.cursor.execute("INSERT INTO data (adminname, filename) VALUES (?, ?)", (adminname, filename))
        self.conn.commit()

    def insert_user(self, username, email, phone, created_at, filename):
        self.cursor.execute(
            "INSERT INTO users (username, email, phone, created_at, filename) VALUES (?, ?, ?, ?, ?)",
            (username, email, phone, created_at, filename)
        )
        self.conn.commit()

    def insert_log(self, adminname, filename, action, status, number_of_records):
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            "INSERT INTO logs (adminname, filename, action, status, number_of_records, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (adminname, filename, action, status, number_of_records, created_at)
        )
        self.conn.commit()
    
    def get_user_by_file(self, filename):
        self.cursor.execute("SELECT * FROM users WHERE filename = ?", (filename,))        
        
        return self.cursor.fetchall()
        
    def get_file_by_adminname(self, adminname):
        self.cursor.execute("SELECT * FROM data WHERE adminname = ?", (adminname,))
        return self.cursor.fetchall()
    
    def close(self):
        self.conn.close()


