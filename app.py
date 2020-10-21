from flask import Flask, render_template
from flask_httpauth import HTTPDigestAuth
from lms import mark_attendance
import mysql.connector
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

@app.route('/view/')
@app.route('/view/<full>')
@auth.login_required
def view(full=False):
    try:
        cnx = mysql.connector.connect(user='RtYeNviJ13', password='GEIeh9z3Wx',
                                    host='remotemysql.com',
                                    port=3306,
                                    database='RtYeNviJ13')
        cursor = cnx.cursor()
        if(full):
            query = ("SELECT * FROM lmslog")
        else:
            query = ("SELECT * FROM lmslog LIMIT 50")

        cursor.execute(query)
        tbody=""
        for row in cursor:
            tbody+="<tr><td>"
            tbody+="</td><td>".join(map(str,row))
            tbody+="</td></tr>"

        return render_template("view.html", tbody = tbody)
    except mysql.connector.Error as err:
        return str(err)
    finally:
        cnx.close()

if __name__ == '__main__':
   app.run(debug=True)