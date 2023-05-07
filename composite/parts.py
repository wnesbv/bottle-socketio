
import datetime as delta
from datetime import datetime
from pathlib import Path, PurePosixPath

import os, sqlite3, jwt, functools
from bottle import (
    request,
    redirect,
    static_file,
    Bottle,
    HTTPError,
)

from dotenv import load_dotenv


load_dotenv(dotenv_path=os.getenv("dotenv_path"))
DOMEN = os.getenv("DOMEN")
JWT_KEY = os.getenv("JWT_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
EMAIL_TOKEN_EXPIRY_MINUTES = os.getenv("EMAIL_TOKEN_EXPIRY_MINUTES")

DATE_TIME = "%d-%m-%Y %H:%M:%S"
dte_str = datetime.now()
f_dt = dte_str.strftime(DATE_TIME)

time_end = (datetime.now() + delta.timedelta(minutes=5),)

key = JWT_KEY
algorithm = JWT_ALGORITHM
domen = DOMEN
token_expiration = EMAIL_TOKEN_EXPIRY_MINUTES


def who_is_who():
    if request.get_cookie("visited"):
        in_code = request.get_cookie("visited")
        item_user = jwt.decode(in_code, key, algorithm)

        is_id = item_user["id"]
        is_name = item_user["name"]
        is_mail = item_user["mail"]
        who_is = [is_id, is_name, is_mail]
        return who_is
    return HTTPError(401, "Sorry.. Access denied..!")


def visited():
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*a, **ka):
            if request.get_cookie("visited"):
                return func(*a, **ka)
            return HTTPError(401, "Sorry.. Access denied..!")

        return wrapper

    return decorator


# ..


parts = Bottle()

con = sqlite3.connect("sqlite.db")
con.row_factory = sqlite3.Row
# ..


# .. static
@parts.route("/<filepath:path>")
def server_static(filepath):
    return static_file(filepath, root="./static")


def post_file(to_id):
    data = (to_id,)
    cur = con.cursor()
    sql = "SELECT upload FROM  blog_table WHERE id=?"
    res = cur.execute(sql, data)
    row = res.fetchone()
    row.keys()
    con.commit()
    cur.close()
    return row["upload"]


# .. chat


@parts.post("/upload-chat")
def img_path():
    user = who_is_who()[0]
    upload = request.files.get("upload")
    # ..
    save_path = f"./static/chat/{user}"
    file_path = f"{save_path}/{upload.filename}"

    ext = PurePosixPath(upload.filename).suffix

    if ext not in (".png", ".jpg", ".jpeg"):
        print("Format files: png, jpg, jpeg ..!")
    if Path(file_path).exists():
        print("Error..! File exists..!")
    os.makedirs(save_path, exist_ok=True)

    with open(f"{file_path}", "wb") as fle:
        fle.write(upload.file.read())
    return file_path


# .. creat
@parts.post("/upload")
def img_creat():
    category = request.forms.get("category")
    upload = request.files.get("upload")
    # ..
    save_path = f"./static/{category}"
    file_path = f"{save_path}/{upload.filename}"

    ext = PurePosixPath(upload.filename).suffix

    if ext not in (".png", ".jpg", ".jpeg"):
        return redirect("/messages?msg=Format files: png, jpg, jpeg ..!")
    if Path(file_path).exists():
        return redirect("/messages?msg=Error..! File exists..!")
    os.makedirs(save_path, exist_ok=True)

    with open(f"{file_path}", "wb") as fle:
        fle.write(upload.file.read())
    return file_path


# @parts.post("/upload")
# def img_creat():
#     category = request.forms.get("category")
#     upload = request.files.get("upload")

#     save_path = f"./static/{category}"
#     file_path = f"{save_path}/{upload.filename}"

#     _, ext = os.path.splitext(upload.filename)

#     if ext not in (".png", ".jpg", ".jpeg"):
#         return redirect("/messages?msg=Format Files: png, jpg, jpeg ..!")

#     if os.path.exists(file_path):
#         return redirect("/messages?msg=OSError: File exists..!")
#     os.makedirs(save_path, exist_ok=True)
#     upload.save(file_path)
#     return file_path


# .. upload
@parts.post("/upload")
def img_upload(to_id):
    category = request.forms.get("category")
    upload = request.files.get("upload")

    save_path = f"./static/{category}"
    file_path = f"{save_path}/{upload.filename}"
    file_miss = post_file(to_id)

    _, ext = os.path.splitext(upload.filename)

    if ext not in (".png", ".jpg", ".jpeg"):
        return file_miss

    if not os.path.exists(save_path):
        os.makedirs(save_path, exist_ok=True)
    upload.save(file_path, overwrite=True)

    return file_path
