
import socketio, jwt
import gevent.monkey; gevent.monkey.patch_all()

from bottle import run, Bottle, template, request, GeventServer
from geventwebsocket.handler import WebSocketHandler

from chat.urls import sio, chat
from auth.urls import auth
from composite.parts import parts



app = Bottle()
app.wsgi = socketio.WSGIApp(sio, app.wsgi)

app.mount("/auth", auth)
app.mount("/chat", chat)
app.mount("/static", parts)


@app.route("/")
def index():
    return template("index.html")


if __name__ == "__main__":

    run(
        app,
        host="127.0.0.1",
        port=8080,
        server=GeventServer,
        handler_class=WebSocketHandler,
        reloader=True,
    )
