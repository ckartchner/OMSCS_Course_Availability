from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait  # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC  # available since 2.26.0
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER
from dotenv import load_dotenv  # installed with 'pip install python-dotenv'
from lxml import html
import sys
import os
import unicodedata
import logging
# import logging.handlers
import smtplib

import pickle
import time
import datetime
import sqlite3
import re
from textwrap import dedent  # De indent multi-line string

from apscheduler.schedulers.blocking import BlockingScheduler


"""
Notes:
XPath is the language used to locate nodes in an XML doc


"""

# Probably need to do something about the scope here
logging.basicConfig(
    filename='OMSCS_CA.log',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.DEBUG)
LOGGER.setLevel(logging.WARNING)

# def setup_logging():
#     logging.basicConfig(
#             filename='OMSCS_CA.log',
#             format='%(asctime)s %(levelname)-8s %(message)s',
#             level=logging.DEBUG)
#     # Set Selenium log level
#     # LOGGER.setLevel(logging.WARNING)

def send_email(subject: str="", body: str=""):
    """
    TBD: Setup to use local SMTP server rather than remote

    :return:
    """
    if subject == "":
        subject = "OMSCS reg monitor unspecified error"
    if body == "":
        body = "Unspecified error occurred. Please refer to logs for more info"
    # Lazy load of email. Update later to be function parameters
    load_dotenv(dotenv_path="./.env")
    to_email = os.environ.get('TO_EMAIL')
    from_email = os.environ.get('FROM_EMAIL')
    email_pwd = os.environ.get('EMAIL_PWD')
    email_user = os.environ.get('EMAIL_USER')

    logging.debug('Sending email notification of error')
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(email_user, email_pwd)
    message = f"""\
        From: {from_email}
        To: {to_email}
        Subject: {subject}
        {body}\
        """
    message = dedent(message)
    server.sendmail(
        from_email,
        to_email,
        message)
    server.quit()

def browser_setup():
    """
    General browser config
    """
    # General browser config
    options = Options()
    # Note: deprecated - https://seleniumhq.github.io/selenium/docs/api/py/webdriver_firefox/selenium.webdriver.firefox.options.html
    # options.set_headless(headless=False)
    options.headless = True
    browser = webdriver.Firefox(firefox_options=options)

    # Load cookies ... doesn't help bypass the need for a push
    # browser.implicitly_wait(15)  # wait 15 seconds for any field to appear
    # browser.get("https://buzzport.gatech.edu/cp/home/displaylogin")
    # try:
    #     cookies = pickle.load(open("cookies.pkl", "rb"))
    #     for cookie in cookies:
    #         browser.add_cookie(cookie)
    # except FileNotFoundError:
    #     logging.debug('Cookie Monster is disappointed. No cookies found.')
    # browser.find_element_by_id("login_btn").click()

    return browser

def catchall(function):
    def wrapper(*args, **kwargs):
        try:
            function(*args, **kwargs)
        except:
            # logging.debug("Unhandled error in login")
            logging.exception("Unhandled error in login eh")
            print("Exception caught")
            send_email()
    return wrapper

@catchall
def gt_login(browser, userid, pwd):
    auto_push = False
    logging.debug('Opening login page')
    browser.implicitly_wait(15)  # wait 15 seconds for any field to appear
    # raise ValueError('Testing: user generated exception')
    try:
        # Hasty attempt to avoid error "Malformed URL: can't access dead object.
        # https://stackoverflow.com/questions/47770694/malformed-url-cant-access-dead-object-in-selenium-when-trying-to-open-google
        # Not really sure why it appeared in the first place
        browser.switch_to.default_content()

        browser.get("https://buzzport.gatech.edu/cp/home/displaylogin")
        browser.find_element_by_id("login_btn").click()
    except Exception as e:
        logging.critical(f"Unhandled error at buzzport login. Exception: {e}")
        timestamp = str(datetime.datetime.now())
        browser.save_screenshot(f'./screenshots/Buzzport_attempt_{timestamp}.png')
        raise

    # Login if not already logged in.
    # Note: Not yet able to bypass login
    # Takes a few seconds to bypass if already logged in, but it works
    try:
        browser.find_element_by_id("username").clear()
        browser.find_element_by_id("username").send_keys(userid)
        browser.find_element_by_id("password").clear()
        browser.find_element_by_id("password").send_keys(pwd)
        browser.find_element_by_name("submit").click()
        logging.debug("Password submission path taken")
        if auto_push == False:
            # Ensures remember me for 7 days is selected when push gets sent
            # Doesn't seem to matter though... login info save between sessions not yet working.
            WebDriverWait(browser, 10).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "duo_iframe")))
            # Select "Remember me for 7 days"
            WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.NAME, "dampen_choice")))
            browser.find_element_by_name("dampen_choice").click()
            # Send Push
            WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, ".//button[contains(text(), 'Send Me a Push')]")))
            browser.find_element_by_xpath(".//button[contains(text(), 'Send Me a Push')]").click()
            # Without switching out of the iframe, a "Can't access dead object" error will be thrown with next find attempt
            browser.switch_to.default_content()
            logging.debug("Duo request sent to phone")

    except NoSuchElementException:
        logging.debug("Buzzport login already authenticated")
    except:
        raise

    # Long variable delay here due to waiting for duo authentication
    # timeout in seconds
    WebDriverWait(browser, 120).until(EC.title_is("BuzzPort"))
    # Store login cookies
    # pickle.dump(browser.get_cookies(), open("cookies.pkl", "wb"))
    browser.find_element_by_xpath(".//a[contains(text(), 'Student')]").click()

def scrape_courses(browser, semester):
    """
    Collect the current status of the course enrollment

    TBD... add link to main buzzport page so this can be recalled

    :param browser: webdriver object
    :param semester: semester name used on OSCAR
    :return: 2d list of all courses
    """
    # Original route went missing during summer 2018, but leaving here as it was shorter path
    route_to_data = 'new'
    # Encountered error below if OSCAR is unavailable (2Aug2018)
    try:
        if route_to_data == "old":
            # This quick link has been broken/missing for June/July Summer 2018
            browser.find_element_by_xpath(".//a[contains(text(), 'Look Up Classes')]"). click()
            # Since the iframe is a separate HTML document embedded in the current
            # one, it is very important to switch to the relevant iframe
            browser.switch_to.frame("the_iframe")
        else:
            browser.find_element_by_xpath(".//a[contains(text(), 'Registration - OSCAR')]").click()
            browser.switch_to.frame("the_iframe")
            browser.find_element_by_name("StuWeb-MainMenuLink").click()
            browser.find_element_by_xpath(".//a[contains(text(), 'Registration')]").click()
            browser.find_element_by_xpath(".//a[contains(text(), 'Look Up Classes')]").click()
    except Exception as e:
        logging.critical(f"OSCAR error. Exception: {e}")
        # TBD - add check for screenshot directory
        # If screenshot directory is missing, the screenshot is silently not saved
        timestamp = str(datetime.datetime.now())
        browser.save_screenshot(f'./screenshots/OSCAR_attempt_{timestamp}.png')
        raise

    # Select Fall 2018, Advanced View, Computer Science, Online courses
    # TBD(1): add check here if the options change
    # TBD(2): add method to easily change semesters

    # Select Fall
    browser.find_element_by_xpath(f"//option[@value={semester}]").click()
    # Submit semester selection
    browser.find_element_by_xpath("//input[@value='Submit']").click()
    # Perform Advanced Search
    browser.find_element_by_xpath("(//input[@name='SUB_BTN'])[2]").click()
    # Select Computer Science Department
    browser.find_element_by_xpath("//option[@value='CS']").click()
    select = Select(browser.find_element_by_id("camp_id"))  # Select Campus
    select.deselect_all()  # If this isn't done, multiple items are selected
    select.select_by_value('O')  # Select only online options
    browser.find_element_by_name("SUB_BTN").click()

    #Scrape table
    html_source = browser.page_source
    parsed = html.fromstring(html_source)
    # Subelements selected below:
    # [0] - tbody
    # [1] - "Sections Found"
    course_table = parsed.xpath('//table[@class="datadisplaytable"]')[0][1]

    # The first element of the table is the "Computer Science" section
    # Second element is the row labeling the columns
    # All remaining elements are rows for each course
    # unicode normalize removes \xa0 and any other potential unicode surprises
    rows = [unicodedata.normalize("NFKD", a.text_content()).split('\n') for a in course_table]

    # Print all rows:
    # print(*rows, sep='\n')
    logging.debug("Scrape complete")
    return rows

def add_to_db(rows, scrape_time, dbname='OMSCS_CA.db'):
    # Check that the dimensions are parsed as expected
    # Needs to be updated with better failure message
    # Failure scenario untested
    row_size = 22
    ue_rows = [row for row in rows[1:] if len(row) != row_size]
    if len(ue_rows) != 0:
        logging.error(f"Bad row lengths found:{len(ue_rows)}")
        logging.error(f"Rows\n{ue_rows}")

    ## Build Table ##
    # conn = sqlite3.connect(':memory:', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    conn = sqlite3.connect(dbname, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cursor = conn.cursor()
    courses = [row[2] for row in rows[2:]]
    semester_prefix = "F18"
    course_tbl = f"courses{semester_prefix}"
    # Sanitize table name. May be useful when semester_prefix is taken as arg
    if not course_tbl.isalnum():
        logging.error(f"Illegal source table name: {course_tbl}")
        exit()
    tb_exists = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{course_tbl}'"
    if not cursor.execute(tb_exists).fetchone():
        # Create table if it does not already exist
        logging.warning(f"{course_tbl} table being created")
        cursor.execute("""
            CREATE TABLE {}(
            Slct,
            CRN,
            Subj,
            Crse,
            Sec,
            Cmp,
            Bas,
            Cred,
            Title,
            Days,
            Time,
            Instructor,
            Location,
            Attribute
            )""".format(course_tbl))
        for row in rows[2:]:
            row_data = row[1:12] + row[18:21]
            cursor.execute("""
                INSERT INTO {}
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""".format(course_tbl),
                           row_data)
    else:
        # Check if course data has changed
        # Schema for handling changes is undefined
        # TBD - testcase with new rows
        # Much work pending here
        for row in rows[2:]:
            crn = row[2]
            row_data = tuple(row[1:12] + row[18:21])
            cursor.execute(f"SELECT * FROM {course_tbl} where CRN='{crn}'")
            tbl_data = cursor.fetchone()
            if row_data != tbl_data:
                logging.warning("Changes to course table rows")
                logging.warning(f"scrape: {row_data}")
                logging.warning(f"db:     {tbl_data}")
                # Add course if change discovered
                # Potential here for runaway course table growth
                # Future should track relation of like rows
                # This section could also be refactored
                cursor.execute("""
                    INSERT INTO {}
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""".format(course_tbl),
                               row_data)

    # Ensure there is no SQL in the course names
    # Highly unlikely, but good practice
    # Also room here to ensure only legal table names attempted
    # Currently ensures starting with letter as tables cannot start with number
    # Testcase TBD
    for course in courses:
        if re.match('^[a-zA-Z][\w]+$', course):
            logging.error(f"Illegal course name found: {course}")
            exit()
    course_tables = [semester_prefix + "_" + course for course in courses]
    enroll_stats = [row[12:18] for row in rows[2:]]

    # Fill in enrollment numbers for each course
    for i in range(0, len(course_tables)):
        course = course_tables[i]
        row_stats = enroll_stats[i]
        row_stats.insert(0, scrape_time)
        tb_exists = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{course}'"
        if not cursor.execute(tb_exists).fetchone():
            # If table does not exist
            logging.warning(f"{course} table being created")
            # Create table for a course
            cursor.execute("""
                CREATE TABLE {}(
                Timestamp,
                Cap,
                Act,
                Rem,
                WL_Cap,
                WL_Act,
                WL_Rem
                )""".format(course))
        cursor.execute("""
            INSERT INTO {}
            VALUES (?, ?, ?, ?, ?, ?, ?)""".format(course),
                       row_stats)

    conn.commit()
    conn.close()
    logging.debug("DB fill finished")

def scheduled_actions(browser, semester, userid, pwd):
    """
    Actions taken repeatedly to generate timeseries

    I see potential here for unhandled exceptions if resources unavailable

    :param browser:
    :param semester:
    :return:
    """
    ct = datetime.datetime.now()
    print(f"Taking scheduled action {ct}")
    logging.debug(f"Preforming scheduled actions on {semester}")
    gt_login(browser, userid, pwd)
    rows = scrape_courses(browser, semester)
    scrape_time = datetime.datetime.now()
    add_to_db(rows, scrape_time)



def coordinator(userid, pwd, semester='201808'):
    """
    Coordinates high level actions scraper

    :param userid:
    :param pwd:
    :param semester:
    :return:
    """
    logging.debug("Running main code")
    # setup_logging()
    browser = browser_setup()
    scheduler = BlockingScheduler()
    scheduler.add_job(scheduled_actions,
                      args=[browser, semester, userid, pwd],
                      trigger='interval',
                      minutes=30,
                      next_run_time=datetime.datetime.now())
    try:
        print("Starting scheduler")
        print('Press Ctrl+C to exit')
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass


def bad_args():
    """
    Behavior to be followed if bad arguments are used when CLI called
    """
    print("Invalid arguments")
    print("This scrip can be called by supplying the username and password")
    print("From the CLI,")
    print("EG: python OMSCS_course_availability.py username password")
    print("Or")
    print("By setting up a .env file (recommended)")
    exit()

def cli_actions():
    """
    Actions to take only when run as a script.

    Can be called with username and password as CLI arguments
    OR
    With username and password as elements of local .env file

    Added .env per recommendation in Miguel Grinberg's 2018 PyCon talk
    https://www.youtube.com/watch?v=2uaTPmNvH0I
    """
    if len(sys.argv) == 1:
        # If no CLI arguments, check local .env
        load_dotenv(dotenv_path="./.env")
        userid = os.environ.get('OMS_ID')
        pwd = os.environ.get('OMS_PWD')
        ba = 0
        if (userid is None):
            print("Could not find OMS_ID in .env")
            ba += 1
        elif (pwd is None):
            print("Could not find OMS_PWD in .env")
            ba += 1
        if ba > 0:
            bad_args()
        coordinator(userid, pwd)
    elif len(sys.argv) == 3:
        # Actions if username and password supplied as CLI arguments
        userid = sys.argv[1]
        pwd = sys.argv[2]
        coordinator(userid, pwd)


if __name__ == "__main__":
    cli_actions()
    # try:
    #     cli_actions()
    # except Exception as e:
    #     send_email()
    #     print("Exception occurred, exiting!")
    #     exit()
    #     # logger.exception('Unhandled Exception')

