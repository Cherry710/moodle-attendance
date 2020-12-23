from flask import Flask, render_template, request
from flask_httpauth import HTTPDigestAuth
from lms import mark_attendance
from celery import Celery
import connection
import os
from prettytable import from_db_cursor
import time


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL'],
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


app = Flask(__name__)

REDIS_URL = os.environ['REDIS_URL'] if os.environ.get(
    'REDIS_URL', None) else "redis://localhost:6379/0"
app.config.update(
    CELERY_BROKER_URL=REDIS_URL,
    CELERY_RESULT_BACKEND=REDIS_URL,
)
celery = make_celery(app)

app.config['SECRET_KEY'] = 'parleg'
auth = HTTPDigestAuth()

users = {
    os.environ.get('HTTP_USER', 'admin'): os.environ.get('HTTP_PASS', 'admin123')
}


@auth.get_password
def get_pw(username):
    if username in users:
        return users.get(username)
    return None


@app.route('/')
def home():
    return "You don't belong here, Kindly leave.!"


@app.route('/subject/<subject>')
def mark(subject):
    queue = []
    for _, username, password in connection.get_users():
        queue.append(mark_async.delay(username, password, subject))
    for q in queue:
        q.get()
    return f"Request Received for {subject}"


@celery.task(name="process_mark_attendance")
def mark_async(username, password, subject):
    try:
        time.sleep(35)
        return mark_attendance(username, password, subject)
    except Exception as e:
        print("APP_ERROR:"+str(e))


@app.route('/view/')
@auth.login_required
def view():
    limit = request.args.get('limit', default=0, type=int)
    wkey = request.args.get('wkey', default=None, type=str)
    wvalue = request.args.get('wvalue', default=None, type=str)
    console = request.args.get('console', default=False, type=bool)
    try:
        cnx = connection.get_connector()
        cursor = cnx.cursor()
        query = connection.get_view_log_query(limit, wkey, wvalue)
        cursor.execute(query)
        if(console):
            mytable = from_db_cursor(cursor)
            ret = mytable.get_string()
        else:
            tbody = ""
            for row in cursor:
                tbody += "<tr><td>"
                tbody += "</td><td>".join(map(str, row))
                tbody += "</td></tr>"

            ret = render_template("view.html", tbody=tbody)
        cursor.close()
        cnx.close()
        return ret
    except Exception as e:
        return str(e)

# NOTE: URL ENCODE BEFORE PASSING THE PASSWORD


@app.route('/add/')
@auth.login_required
def add_user():
    sid = request.args.get('sid', default=None, type=str)
    password = request.args.get('password', default=None, type=str)
    return f"{sid} is Added" if connection.insert_user(sid, password) else f"{sid} is NOT Added"


@app.route('/delete/')
@auth.login_required
def delete_user():
    sid = request.args.get('sid', default=None, type=str)
    return f"{sid} is Deleted" if connection.delete_user(sid) else f"{sid} is NOT Deleted"


if __name__ == '__main__':
    app.run(debug=True)

# on github
