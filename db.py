
import sqlite3
from data import db_user, db_chat, db_journal

con = sqlite3.connect("sqlite.db")


def creat_table():
    cur = con.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS user_table(
            id INTEGER PRIMARY KEY,
            name TEXT VARCHAR(30) UNIQUE NOT NULL,
            mail TEXT VARCHAR(30) UNIQUE NOT NULL,
            password TEXT NOT NULL,
            upload TEXT,
            email_verified BOOLEAN DEFAULT(FALSE),
            is_active  BOOLEAN DEFAULT(FALSE),
            generated DATETIME NOT NULL,
            changed DATETIME);
        CREATE TABLE IF NOT EXISTS chat_table(
            id INTEGER PRIMARY KEY,
            story TEXT VARCHAR(200),
            choice_room TEXT VARCHAR(30),
            upload TEXT,
            generated DATETIME,
            changed DATETIME,
            user_list INTEGER,
            FOREIGN KEY(user_list) REFERENCES user_table(id));
        CREATE TABLE IF NOT EXISTS journal(
            id INTEGER PRIMARY KEY,
            user_list TEXT,
            choice_room TEXT VARCHAR(30),
            connect DATETIME,
            disconnect DATETIME);
        CREATE TRIGGER tg_limit 
        BEFORE INSERT ON journal
        FOR EACH ROW
        WHEN 10 < (SELECT COUNT(*) FROM journal) + 1
        BEGIN
          DELETE FROM journal;
        END;
        """
    )
    cur.executemany(
        "INSERT INTO user_table (name, mail, password, generated) VALUES(?,?,?,?)", db_user)
    cur.executemany(
        "INSERT INTO chat_table (story, generated, user_list) VALUES(?,?,?)", db_chat)
    cur.executemany(
        "INSERT INTO journal (user_list, connect, disconnect) VALUES(?,?,?)", db_journal)
    con.commit()
    con.close()



creat_table()
