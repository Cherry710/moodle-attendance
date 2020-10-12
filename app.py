from flask import Flask, render_template
from flask_httpauth import HTTPDigestAuth
from lms import mark_attendance
app = Flask(__name__)
app.config['SECRET_KEY'] = 'parleg'
auth = HTTPDigestAuth()

users = {
    "suman": "rgukt123",
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
    return mark_attendance(subject)

@app.route('/view')
@auth.login_required
def view():
    with open("log.csv", "r") as logfile:
        CSV_SEPERATOR = ","
        tbody=""
        for row in logfile.readlines()[::-1]:
            tbody+=("<tr>" + "".join([f"<td>{x}</td>" for x in row.split(CSV_SEPERATOR)]) + "</tr>")
    return render_template("view.html", tbody = tbody)


if __name__ == '__main__':
   app.run(debug=True)