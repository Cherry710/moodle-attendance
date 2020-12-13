from requests import Session
from bs4 import BeautifulSoup as bs
import datetime
import connection

subject_links = {
    "MC"    :   "http://lms.rgukt.ac.in/mod/attendance/view.php?id=741",
    "BC"    :   "http://lms.rgukt.ac.in/mod/attendance/view.php?id=987",
    "IS"    :   "http://lms.rgukt.ac.in/mod/attendance/view.php?id=939",
    "QC"    :   "http://lms.rgukt.ac.in/mod/attendance/view.php?id=6352",
    "MEFA"  :   "http://lms.rgukt.ac.in/mod/attendance/view.php?id=2307",
}

LOGIN_PAGE = "http://lms.rgukt.ac.in/login/index.php"


def mark_attendance(subject): 
    logging = []
    IS_SUCCESS = False
    IS_LOGGING_DONE = False
    COUNT = 0
    try:
        #result | timestamp | ID  | subject | msg
        cnx = connection.get_connector() 
        insert_log_query = connection.INSERT_LOG_QUERY
        cursor = cnx.cursor()
        for _,username,password in connection.get_users():
            with Session() as s:

                login_page_content = bs(s.get(LOGIN_PAGE).content, "html.parser")
                logintoken = login_page_content.find("input", {"name":"logintoken"})["value"]
                login_data = {"username":username,"password":password, "logintoken":logintoken}

                res = s.post(LOGIN_PAGE,login_data)
                if(res.status_code!=200):
                    log = ("ERROR",str(datetime.datetime.now()),username,subject,f"returned code:{res.status_code}")
                    continue

                attendace_page = s.get(subject_links[subject])
                att_content = bs(attendace_page.content, "html.parser")
                x = att_content.select('a[href*="sessid="]')
                if(len(x)==0):
                    log = ("ERROR",str(datetime.datetime.now()),username,subject, "'Submit Attendance' not found")
                    continue

                att_link = x[0]['href']
                

                form_site = s.get(att_link)
                form_bs = bs(form_site.content,"html.parser")
                spans = form_bs.select(".statusdesc")
                
                att_link = att_link.split("?")[1]
                att_dict = {x[0] : x[1] for x in [x.split("=") for x in att_link.split("&") ]}

                got_present = False
                button_val=0
                button_text="None"
                for span in spans:
                    if(span.get_text()=="Present"):
                        button_text=span.get_text()
                        button_val = span.parent.input['value']
                        got_present = True
                if(not got_present):
                    for span in spans:
                        if(span.get_text()=="Late"):
                            button_text=span.get_text()
                            button_val = span.parent.input['value']

                if(button_val):
                    post_data = {
                        "MoodleSession" :   s.cookies.get_dict()["MoodleSession"],
                        "sessid"        :   att_dict["sessid"],
                        "sesskey"       :   att_dict["sesskey"],
                        "_qf__mod_attendance_student_attendance_form"   :   1,
                        "mform_isexpanded_id_session"   :   1,
                        "status"        :   button_val,
                        "submitbutton"  :   "Save changes"
                    }
                    final_resp = s.post("http://lms.rgukt.ac.in/mod/attendance/attendance.php",post_data)
                    if(final_resp.status_code==200):
                        log = ("SUCCESS",str(datetime.datetime.now()),username,subject,f"marked as {button_text}")
                        IS_SUCCESS = True
                        COUNT+=1
                    else:
                        log = ("ERROR",str(datetime.datetime.now()),username,subject,f"returned code:{res.status_code}")
                else:
                    log = ("ERROR",str(datetime.datetime.now()),username,subject,"Present or Late not found")

                cursor.execute(insert_log_query, log)
        
        cnx.commit()
        cursor.close()
        cnx.close()
        IS_LOGGING_DONE = True
    except Exception as e:
        print(e)       

    if(IS_SUCCESS):
        return f"OK - {COUNT}"
    elif(not IS_LOGGING_DONE):
        return f"LOG ERR-OK:{COUNT}"
    else:
        return "NOT"