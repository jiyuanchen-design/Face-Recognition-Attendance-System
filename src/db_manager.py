import sqlite3
import datetime
from config import DATABASE_PATH

class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()

    def _connect(self):
        self.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def _create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                feature_vector BLOB NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                name TEXT NOT NULL,
                check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT
            )
        ''')
        self.conn.commit()

    def add_student(self, student_id, name, feat):
        try:
            self.cursor.execute(
                "INSERT INTO students (student_id, name, feature_vector) VALUES (?, ?, ?)",
                (student_id, name, feat)
            )
            self.conn.commit()
            return True, "注册成功"
        except sqlite3.IntegrityError:
            return False, "学号已存在"

    def delete_student(self, sid):
        self.cursor.execute("DELETE FROM students WHERE student_id=?", (sid,))
        self.conn.commit()

    def clear_all_students(self):
        self.cursor.execute("DELETE FROM students")
        self.conn.commit()

    def get_all_features(self):
        self.cursor.execute("SELECT student_id, name, feature_vector FROM students")
        return self.cursor.fetchall()

    def get_all_students(self):
        self.cursor.execute("SELECT student_id, name FROM students")
        return self.cursor.fetchall()

    def add_attendance_record(self, sid, name, status):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            "INSERT INTO attendance_records (student_id,name,check_in_time,status) VALUES (?,?,?,?)",
            (sid, name, now, status)
        )
        self.conn.commit()

    def get_today_attendance(self):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute(
            "SELECT student_id,name,check_in_time,status FROM attendance_records WHERE DATE(check_in_time)=?"
            " ORDER BY check_in_time DESC",
            (today,)
        )
        return self.cursor.fetchall()

    def get_member_status(self, sid, today):
        # 拿到今天最后一条记录
        self.cursor.execute('''
            SELECT status FROM attendance_records
            WHERE student_id=? AND DATE(check_in_time)=?
            ORDER BY check_in_time DESC LIMIT 1
        ''', (sid, today))
        res = self.cursor.fetchone()

        if not res:
            return "未签到"

        last_status = res[0]

        # 关键逻辑：最后一条是签退完成 → 显示未签到
        if last_status == "签退完成":
            return "未签到"
        else:
            return last_status

    def reset_all_records(self):
        self.cursor.execute("DELETE FROM attendance_records")
        self.conn.commit()