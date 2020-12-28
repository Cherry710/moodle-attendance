import mysql.connector
from mysql.connector import errorcode
import os


def get_insert_log_query():
    INSERT_LOG_QUERY = (
        "INSERT INTO lmslog(result, timestamp, sid, subject, msg) VALUES (%s, %s, %s, %s, %s)")
    return INSERT_LOG_QUERY


def get_view_log_query(limit=0, wkey=None, wvalue=None):
    query_string = "SELECT * FROM lmslog"
    query_string += f" WHERE {wkey}='{wvalue}'" if (wkey and wvalue) else ""
    query_string += " ORDER BY id DESC"
    query_string += f" LIMIT {limit}" if limit else ""
    VIEW_LOG_QUERY = (query_string)
    return VIEW_LOG_QUERY


def get_users(hostid):
    try:
        cnx = get_connector()
        GET_USERS_QUERY = (f"SELECT * FROM users WHERE hostid={hostid}")
        cursor = cnx.cursor()
        cursor.execute(GET_USERS_QUERY)
        res = [row for row in cursor]
        cnx.commit()
        cursor.close()
        cnx.close()
        return res
    except Exception as e:
        print(e)
        return []


def insert_user(sid, password):
    if(not(sid and password)):
        return False
    try:
        cnx = get_connector()
        INSERT_USER_QUERY = (
            "INSERT INTO users( sid,  password) VALUES (%s, %s)")
        cursor = cnx.cursor()
        cursor.execute(INSERT_USER_QUERY, (sid, password))
        cnx.commit()
        cursor.close()
        cnx.close()
        return True
    except Exception as e:
        print(e)
        return False


def delete_user(sid):
    if(not sid):
        return False
    try:
        cnx = get_connector()
        DELETE_USER_QUERY = (f"DELETE FROM users WHERE sid='{sid}'")
        cursor = cnx.cursor()
        cursor.execute(DELETE_USER_QUERY)
        cnx.commit()
        cursor.close()
        cnx.close()
        return True
    except Exception as e:
        print(e)
        return False


def get_connector():
    try:
        cnx = mysql.connector.connect(user=os.environ.get('DB_USER', 'root'),
                                      password=os.environ.get('DB_PASS', ''),
                                      host=os.environ.get(
                                          'DB_HOST', 'localhost'),
                                      port=3306,
                                      database=os.environ.get('DB_DB', 'lms-attendace'))
        return cnx
    except mysql.connector.Error as err:
        print(str(err))
        raise
