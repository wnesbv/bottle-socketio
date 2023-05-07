
from datetime import datetime, timedelta
import os, sqlite3, bcrypt, jwt

from bottle import (
    get,
    post,
    view,
    route,
    abort,
    request,
    response,
    redirect,
    template,
    Bottle,
    HTTPError,
)
from smtp_mail.verify import send_mail
from composite.parts import (
    con,
    key,
    f_dt,
    domen,
    algorithm,
    who_is_who,
    token_expiration,
)


auth = Bottle()


def match_mail(mail):
    data = (mail,)
    cur = con.cursor()
    sql = "SELECT mail FROM user_table WHERE mail=?"
    in_sql = cur.execute(sql, data)
    res = in_sql.fetchone() is None
    cur.close()
    return res


def match_name_mail(name, mail):
    data = name, mail
    cur = con.cursor()
    sql = "SELECT name FROM user_table WHERE name=? OR mail=?"
    in_sql = cur.execute(sql, data)
    res = in_sql.fetchone() is None
    cur.close()
    return res


def check_email_verified(mail):
    data = (mail,)
    cur = con.cursor()
    sql = "SELECT email_verified FROM user_table WHERE mail=?"
    res = cur.execute(sql, data)
    row = res.fetchone()
    row.keys()
    cur.close()
    return row


@auth.route("/register")
def user_register():
    return template("auth/register.html")


@auth.post("/register")
def auth_register():
    name = request.forms.get("name")
    mail = request.forms.get("mail")
    pswd = request.forms.get("password")
    # ..
    res = match_name_mail(name, mail)

    if res:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pswd.encode(), salt)
        # ..
        data = (
            name,
            mail,
            hashed,
            f_dt,
        )
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO user_table (
                name, mail, password, generated
            )VALUES (?,?,?,?)
            """,
            data,
        )
        con.commit()
        cur.close()
        # ..
        payload = {
            "mail": mail,
            "exp": datetime.utcnow()
            + timedelta(minutes=int(token_expiration)),
            "iat": datetime.utcnow(),
            "scope": "email_verification",
        }
        token = jwt.encode(payload, key, algorithm)
        # ..
        verify = mail
        send_mail(
            f"Follow the link, confirm your email - {domen}/auth/verify-email?token={token}",
            verify,
        )
        # ..
        return redirect("/messages?msg=Go to the specified email address..")
    return HTTPError(401, "Sorry..")


# verify..
def token_verify():
    token = request.query["token"]
    try:
        payload = jwt.decode(token, key, algorithm)

        if payload["scope"] == "email_verification":
            mail = payload["mail"]
            return mail
        return HTTPError(401, "Invalid scope for token")

    except jwt.ExpiredSignatureError as exc:
        raise HTTPError(401, "Email token expired") from exc
    except jwt.InvalidTokenError:
        raise HTTPError(401, "Invalid name or mail token") from exc


@auth.route("/verify-email")
def mail_verify():
    mail = token_verify()
    res = match_mail(mail)
    row = check_email_verified(mail)
    if res:
        return HTTPError(401, "Invalid user..! Please create an account")
    if row["email_verified"] == 1:
        return redirect("/messages?msg=Email has already been verified!..")
    # ..
    email_verified = 1
    is_active = 1
    data = email_verified, is_active, mail
    cur = con.cursor()
    sql = "UPDATE user_table SET email_verified=?, is_active=? WHERE mail=?"
    cur.execute(sql, data)
    con.commit()
    cur.close()

    return redirect("/")


# login..
@auth.route("/login")
def user_login():
    return template("auth/login.html")


@auth.post("/login")
def auth_login():
    mail = request.forms.get("mail")
    pswd = request.forms.get("password")

    if match_mail(mail) is False:
        cur = con.cursor()
        data = (mail,)
        sql = "SELECT id, name, mail, password FROM user_table WHERE mail=?"
        res = cur.execute(sql, data)
        row = res.fetchone()
        row.keys()
        cur.close()
        if bcrypt.checkpw(pswd.encode(), row["password"]):
            payload = {
                "id": row["id"],
                "name": row["name"],
                "mail": row["mail"],
            }

            visited = jwt.encode(payload, key, algorithm)
            response.set_cookie(
                "visited",
                visited,
                path="/",
                httponly=True,
            )
            return redirect("/")
        return HTTPError(401, "Sorry.. The password doesn't match..!")
    return HTTPError(401, "Sorry.. NO user..!")


# ..
@auth.route("/hello")
def hello_again():
    if request.get_cookie("visited"):
        while 1:
            in_code = request.get_cookie("visited")

            item_user = jwt.decode(in_code, key, algorithm)

            name = item_user["name"]
            who_is = who_is_who()[2]

            return template(
                "Hello (item list).. - {{item_user}} name.. - {{name}} in_code - {{in_code}} who_is.. - {{who_is}}",
                item_user=item_user,
                name=name,
                in_code=in_code,
                who_is=who_is,
            )
    return HTTPError(401, "Sorry..")
