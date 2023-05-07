
import bcrypt
from composite.parts import f_dt


salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(b"password", salt)


db_user = [
    ("First user name", "one@gmail.com", hashed, f"{f_dt}"),
    ("Second user name", "two@gmail.com", hashed, f"{f_dt}"),
]
db_chat = [
    ("First chat story", f"{f_dt}", "1"),
    ("Second chat story", f"{f_dt}", "2"),
]
db_journal = [
    ("one@gmail.com", f"{f_dt}", f"{f_dt}"),
    ("two@gmail.com", f"{f_dt}", f"{f_dt}"),
]
