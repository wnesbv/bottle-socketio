from datetime import datetime
import socketio, json, jwt
from bottle import template, request, Bottle
from composite.parts import con, f_dt, visited, who_is_who


chat = Bottle()


F_TIME = "%d-%m %H:%M %S"
JWT_ALGORITHM = "HS256"
JWT_KEY = "!0_77!%_#)p3gk-m_np8sukvi1^9_^38s^l-g505fsqg-1j&2&"


# ..


sio = socketio.Server(
    logger=True,
    async_mode="gevent",
    cookie=("userio")
)


# ..


def user_visited(headers):
    user_cookie = headers["HTTP_COOKIE"]

    removed = user_cookie.replace(";", "")
    i_token = dict(i.split("=") for i in removed.split())
    token = i_token.get("visited")

    coockie_visited = jwt.decode(token, JWT_KEY, JWT_ALGORITHM)
    for_user = coockie_visited["mail"]

    # print("user visited..! {}".format(for_user))
    return for_user


def save_msg(story, user):
    i_user = jwt.decode(user, JWT_KEY, JWT_ALGORITHM)
    i_mail = i_user["mail"]

    data = (story, f_dt, i_mail)
    cur = con.cursor()
    sql = "INSERT INTO chat_table (story, generated, user_list)VALUES (?,?,?)"
    cur.execute(sql, data)
    con.commit()
    cur.close()
    return data


# REPLACE
def save_journal(headers):
    start = datetime.now()
    f_start = start.strftime(F_TIME)
    user_list = user_visited(headers)
    data = user_list, f_start
    cur = con.cursor()
    cur.execute(
        """
        INSERT INTO journal (
            user_list, connect
        )VALUES (?,?)
        """,
        data,
    )
    con.commit()
    cur.close()
    return data


def save_img(upload, user):
    i_user = jwt.decode(user, JWT_KEY, JWT_ALGORITHM)
    i_id = i_user["id"]
    img = f"/static/chat/{upload}"

    data = (img, f_dt, i_id)
    cur = con.cursor()
    sql = "INSERT INTO chat_table (upload, generated, user_list)VALUES (?,?,?)"
    cur.execute(sql, data)
    con.commit()
    cur.close()
    return data


# ..


@sio.event
def my_event(sid, message):
    sio.emit("my_response", {"data": message["data"]}, room=sid)


# ..


@sio.event
def my_broadcast_event(sid, message):
    sio.emit("my_response", {"data": message["data"], "user": message["user"]})
    print("broadcast....", message["data"], message["user"])

    dump_msg = json.dumps(message)
    load_msg = json.loads(dump_msg)
    save_msg(load_msg["data"], load_msg["user"])
    print("save msg....")


clients = 0



@sio.event
def connect(sid, headers):

    global clients
    clients += 1


    sio.emit(
        "my_response", {"data": "Connected..!", "count": clients}, room=sid
    )
    sio.emit(
            "entrance", {"email": user_visited(headers)}
        )


    print(f" Client connect..! sid.. {sid} clients.. {clients}")

    save_journal(headers)

    print(f"save journal connect.. {user_visited(headers)} {datetime.now()}")


@sio.event
def my_message(sid, data):
    print(f"message.. (my_message) {data}")


@sio.event
def disconnect(sid):
    global clients
    clients -= 1

    user_cookie = sio.get_environ(sid, "/")["HTTP_COOKIE"]

    removed = user_cookie.replace(";", "")
    i_token = dict(i.split("=") for i in removed.split())
    token = i_token.get("visited")

    coockie_visited = jwt.decode(token, JWT_KEY, JWT_ALGORITHM)
    for_user = coockie_visited["mail"]

    # ..
    sio.emit(
            "exit", {"user": for_user}
        )
    # ..

    print(f" Client disconnected..! sid.. {sid} clients.. {clients}")

    end = datetime.now()
    f_end = end.strftime(F_TIME)
    data = for_user, f_end
    cur = con.cursor()
    cur.execute(
        """
        INSERT INTO journal (
            user_list, disconnect
        )VALUES (?,?)
        """,
        data,
    )
    con.commit()
    cur.close()

    print(f"save journal disconnect.. {for_user} {datetime.now()}")


# ..


@sio.event
def join(sid, message):
    sio.enter_room(sid, message["room"])
    sio.emit("my_response", {"data": "Entered room: " + message["room"]}, room=sid)


@sio.event
def leave(sid, message):
    sio.leave_room(sid, message["room"])
    sio.emit("my_response", {"data": "Left room: " + message["room"]}, room=sid)


@sio.event
def close_room(sid, message):
    sio.emit(
        "my_response",
        {"data": "Room " + message["room"] + " is closing."},
        room=message["room"],
    )
    sio.close_room(message["room"])


@sio.event
def my_room_event(sid, message):
    sio.emit("my_response", {"data": message["data"]}, room=message["room"])


# ..


@sio.event
def disconnect_request(sid):
    sio.disconnect(sid)
    print(f"disconnect_request.. {sid}")


# ..


@chat.route("/")
@visited()
def chat_all_get():
    token = request.get_cookie("visited")
    user_list = who_is_who()[2]
    # ..
    cur = con.cursor()
    cur.execute("SELECT * FROM chat_table")
    res = cur.fetchall()
    cur.execute("SELECT * FROM journal ORDER BY - id")
    i_journal = cur.fetchall()
    cur.close()
    return template(
        "chat/chat.html",
        res=res,
        token=token,
        user_list=user_list,
        i_journal=i_journal,
    )
