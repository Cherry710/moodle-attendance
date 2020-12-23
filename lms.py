from requests import Session
from bs4 import BeautifulSoup as bs
import datetime
import connection

LOGIN_PAGE = "http://lms.rgukt.ac.in/login/index.php"
BASE_LINK = "http://lms.rgukt.ac.in/mod/attendance/view.php?id="
subject_links = {
    "MC":   BASE_LINK + "741",
    "BC":   BASE_LINK + "987",
    "IS":   BASE_LINK + "939",
    "QC":   BASE_LINK + "6352",
    "MEFA":   BASE_LINK + "2307",
}


def getlocaltime(): return datetime.datetime.now(
    datetime.timezone(datetime.timedelta(hours=5, minutes=30))).strftime("%c")


def submit_attendance(link_component, sess):
    IS_SUCCESS = False

    spans, att_dict = get_spans_and_att_dict(link_component, sess)

    button_val, button_text = get_button(spans)

    if(button_val):
        final_resp = sess.post(
            "http://lms.rgukt.ac.in/mod/attendance/attendance.php", get_post_data(sess, att_dict, button_val))

        if(final_resp.status_code == 200):
            log = ("SUCCESS", getlocaltime(), username,
                   subject, f"marked as {button_text}")
            IS_SUCCESS = True
        else:
            log = ("ERROR", getlocaltime(), username, subject,
                   f"returned code:{res.status_code}")
    else:
        log = ("ERROR", getlocaltime(), username,
               subject, "Present or Late not found")

    return IS_SUCCESS, log


def get_spans_and_att_dict(link_component, sess):
    att_link = link_component[0]['href']
    form_site = sess.get(att_link)
    form_bs = bs(form_site.content, HTML_PARSER)
    spans = form_bs.select(".statusdesc")

    att_link = att_link.split("?")[1]
    att_dict = {link_component[0]: link_component[1] for link_component in [
        link_component.split("=") for link_component in att_link.split("&")]}
    return spans, att_dict


def get_post_data(sess, att_dict, button_val):
    post_data = {
        "MoodleSession":   sess.cookies.get_dict()["MoodleSession"],
        "sessid":   att_dict["sessid"],
        "sesskey":   att_dict["sesskey"],
        "_qf__mod_attendance_student_attendance_form":   1,
        "mform_isexpanded_id_session":   1,
        "status":   button_val,
        "submitbutton":   "Save changes"
    }
    return post_data


def get_button(spans):
    got_present = False
    button_val = 0
    button_text = "None"
    for span in spans:
        if(span.get_text() == "Present"):
            button_text = span.get_text()
            button_val = span.parent.input['value']
            got_present = True

    if(not got_present):
        for span in spans:
            if(span.get_text() == "Late"):
                button_text = span.get_text()
                button_val = span.parent.input['value']

    return button_val, button_text


def mark_user(username, password, subject):

    with Session() as sess:
        sess.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
        })

        login_data = get_login_data(sess, username, password)

        res = sess.post(LOGIN_PAGE, login_data)
        if(res.status_code != 200):
            return False, ("ERROR", getlocaltime(), username, subject, f"returned code:{res.status_code}")

        link_component = get_subject_link_component(sess, subject)

        if(len(link_component) == 0):
            return False, ("ERROR", getlocaltime(), username, subject, "'Submit Attendance' not found")

        return submit_attendance(link_component, sess)


def get_subject_link_component(sess, subject):
    HTML_PARSER = "html.parser"
    attendace_page = sess.get(subject_links[subject])
    att_content = bs(attendace_page.content, HTML_PARSER)
    link_component = att_content.select('a[href*="sessid="]')
    return link_component


def get_login_data(sess, username, password):
    HTML_PARSER = "html.parser"
    login_page_content = bs(sess.get(LOGIN_PAGE).content, HTML_PARSER)
    logintoken = login_page_content.find(
        "input", {"name": "logintoken"})["value"]
    login_data = {"username": username,
                  "password": password, "logintoken": logintoken}
    return login_data


def mark_attendance(username, password, subject):
    try:
        IS_SUCCESS = mark_and_log(username, password, subject)
    except Exception as e:
        print(f"EXCEPTION - {str(e)}")

    if(IS_SUCCESS):
        return f"OK - {username}"
    else:
        return f"NOT - {username}"


def mark_and_log(username, password, subject):
    # result | timestamp | ID  | subject | msg
    cnx = connection.get_connector()
    insert_log_query = connection.get_insert_log_query()
    cursor = cnx.cursor()

    IS_SUCCESS, log = mark_user(username, password, subject)
    cursor.execute(insert_log_query, log)
    cnx.commit()

    cursor.close()
    cnx.close()
    return IS_SUCCESS
