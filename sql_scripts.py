import sqlite3
from config import *


def data_insert():
    conn = sqlite3.connect(data_base)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO user (user_id, username, rights, date_end_sub, active_task) VALUES(?, ?, ?, ?, ?)", (user_id, username, 0, None, 0,))

    conn.commit()
    conn.close()