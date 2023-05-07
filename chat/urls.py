
from datetime import datetime
import socketio, json, jwt
from bottle import (
    template,
    request,
    Bottle
)
from composite.parts import con, f_dt, visited, who_is_who


chat = Bottle()


F_TIME = "%d-%m %H:%M %S"
JWT_ALGORITHM = "HS256"
JWT_KEY = "!0_77!%_#)p3gk-m_np8sukvi1^9_^38s^l-g505fsqg-1j&2&"


# ..


sio = socketio.Server(
    logger=True,
    async_mode="gevent",
    # cookie=("userio") + '=' + user_io()
)


# ..


def user_visited(environ):
    user_cookie = environ["HTTP_COOKIE"]

    original = user_cookie
    removed = original.replace("visited=", "")

    item_user = jwt.decode(removed, JWT_KEY, JWT_ALGORITHM)
    for_user = item_user["mail"]

    print("user visited..! {}".format(for_user))
    return str(for_user)


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
def save_journal(environ):
    start = datetime.now()
    f_start = start.strftime(F_TIME)
    user_list = user_visited(environ)
    data = user_list, f_start
    cur = con.cursor()
    cur.execute(
        """
        INSERT INTO journal (
            user_list, connect
        )VALUES (?,?)
        """,
        data
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


# ..


@sio.event
def my_event(sid, message):
    sio.emit("my_response", {"data": message["data"]}, room=sid)

# ..


@sio.event
def my_broadcast_event(sid, message):
    sio.emit(
        "my_response", {"data": message["data"], "user": message["user"]}
    )
    print("broadcast....", message["data"], message["user"])

    dump_msg = json.dumps(message)
    load_msg = json.loads(dump_msg)
    save_msg(load_msg["data"], load_msg["user"])
    print("save msg....")


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

@sio.event
def disconnect_request(sid):
    sio.disconnect(sid)
    print("disconnect_request..", sid)


# ..


@sio.event
def connect(sid, environ):
    sio.emit("my_response", {"data": "Connected", "count": 0}, room=sid)

    print("connect.. {}".format(sid))
    print("user environ.. {}".format(user_visited(environ)))

    save_journal(environ)
    print("save journal connect.. {} timme.. {}".format(user_visited(environ), datetime.now()))



@sio.event
def my_message(sid, data):
    print('message.. (my_message)' , data)

@sio.event
def disconnect(sid):
    print("Client disconnected..", sid)

    user_cookie = sio.get_environ(sid, "/")["HTTP_COOKIE"]

    original = user_cookie
    removed = original.replace("visited=", "")

    item_user = jwt.decode(removed, JWT_KEY, JWT_ALGORITHM)
    for_user = item_user["mail"]

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
        data
    )
    con.commit()
    cur.close()

    print("save journal disconnect.. {} timme.. {}".format(for_user, datetime.now()))
