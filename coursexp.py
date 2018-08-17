"""
Library for making interactions with GT registration
a little less painful, and a little more automated.
"""

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait  # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC  # available since 2.26.0
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from dotenv import load_dotenv  # installed with 'pip install python-dotenv'
from lxml import html
# Standard library
from textwrap import dedent  # De indent multi-line string
import os
import unicodedata
import smtplib
import pickle
import datetime
import sqlite3
import re
import logging

# Logging setup as child of __main__
logger = logging.getLogger('__main__.'+__name__)
logger.setLevel(logging.DEBUG)


def logsetup(ilogger, logfile='OMSCS_CA.log'):
    """
    Setup logging for applications using this library

    :param ilogger: Logging object
    :param logfile: File logs will be written to
    :return: Updated logging object
    """
    ilogger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s:%(funcName)-8s:%(levelname)-8s %(message)s')
    # TBD, try rotating file handler
    fh = logging.FileHandler(logfile)
    fh.setFormatter(formatter)
    ilogger.addHandler(fh)
    return ilogger


def send_email(subject: str="", body: str=""):
    """
    Send email notifications

    Primarily used to surface unhandled exceptions
    TBD: Setup to use sendmail or local SMTP server rather than remote

    :param subject: Email subject as string
    :param body: Email body as string
    """
    if subject == "":
        subject = "OMSCS reg monitor unspecified error"
    if body == "":
        body = "Unspecified error occurred. Please refer to logs for more info"
    # Load email addresses and login info through environment variables
    load_dotenv(dotenv_path="./.env")
    to_email = os.environ.get('TO_EMAIL')
    from_email = os.environ.get('FROM_EMAIL')
    email_pwd = os.environ.get('EMAIL_PWD')
    email_user = os.environ.get('EMAIL_USER')

    logger.debug('Sending email notification of error')
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


def browser_setup(headless=True):
    """
    General browser config

    :param headless: Set if headless mode is to be used with the browser
    """
    # General browser config
    options = Options()
    options.headless = headless
    browser = webdriver.Firefox(firefox_options=options)

    # Load cookies ... doesn't help bypass the need for a push
    # browser.implicitly_wait(15)  # wait 15 seconds for any field to appear
    # browser.get("https://buzzport.gatech.edu/cp/home/displaylogin")
    # try:
    #     cookies = pickle.load(open("cookies.pkl", "rb"))
    #     for cookie in cookies:
    #         browser.add_cookie(cookie)
    # except FileNotFoundError:
    #     logger.debug('Cookie Monster is disappointed. No cookies found.')
    # browser.find_element_by_id("login_btn").click()

    return browser


def catchall(fction):
    """
    Decorator which all exceptions raised by function

    Used to add log info, and send email on exception

    :param fction: Function being wrapped
    """
    def wrapper(*args, **kwargs):
        try:
            fction(*args, **kwargs)
        except:
            logger.exception("Unhandled error in login exception handler")
            print("Exception caught")
            send_email()
    return wrapper


@catchall
def gtlogin(browser, auto_push=False, **kwargs):
    """
    Login to buzzport

    If not already logged in:
    Logs in with GTID and credentials
    Makes DUO request -- Requires user interaction

    :param browser: Selenium browser object
    :param auto_push: Flag for Duo 2FA settings. Set true if 2FA request sent
                      immediately on login. False if user needs to manually
                      push 2FA. False recommended as it allows setting the
                      remember me for 7 days flag.
    :param kwargs: Used to optionally take login credentials as arguments
    :return:
    """

    keys = kwargs.keys()
    load_dotenv(dotenv_path="./.env")
    if 'userid' in keys:
        userid = kwargs['userid']
    else:
        userid = os.environ.get('OMS_ID')
    if 'pwd' in keys:
        pwd = kwargs['keys']
    else:
        pwd = os.environ.get('OMS_PWD')

    logger.debug('Opening login page')
    browser.implicitly_wait(15)  # wait 15 seconds for any field to appear

    try:
        # Hasty attempt to avoid error "Malformed URL: can't access dead object.
        # https://stackoverflow.com/questions/47770694/malformed-url-cant-access-dead-object-in-selenium-when-trying-to-open-google
        # Not really sure why it appeared in the first place
        browser.switch_to.default_content()

        browser.get("https://buzzport.gatech.edu/cp/home/displaylogin")
        browser.find_element_by_id("login_btn").click()
    except Exception as e:
        logger.critical(f"Unhandled error at buzzport login. Exception: {e}")
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
        logger.debug("Password submission path taken")
        if auto_push is False:
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
            # Without switching out of the iframe, a "Can't access dead object"
            # error will be thrown with next find attempt
            browser.switch_to.default_content()
            logger.info("Duo request sent to phone")

    except NoSuchElementException:
        logger.debug("Buzzport login already authenticated")
    # Raise exception to catchall. Unnecessary?
    except:
        raise

    # Long variable delay here due to waiting for duo authentication
    # timeout in seconds
    WebDriverWait(browser, 120).until(EC.title_is("BuzzPort"))
    # Store login cookies
    # pickle.dump(browser.get_cookies(), open("cookies.pkl", "wb"))


def _lookup_classes(browser):
    """
    Navigate to lookup classes page

    Called by:
    avail_sems
    gotosem

    :param browser: Selenium webdriver object
    """
    browser.get("https://buzzport.gatech.edu/cps/welcome/loginok.html")
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
        logger.critical(f"OSCAR error. Exception: {e}")
        # TBD - add check for screenshot directory
        # If screenshot directory is missing, the screenshot is silently not saved
        timestamp = str(datetime.datetime.now())
        browser.save_screenshot(f'./screenshots/OSCAR_attempt_{timestamp}.png')
        raise
    return browser


def avail_sems(browser, verbose=False, pkl=True, email_diffs=True):
    """
    BROKEN!!!
    works fine on local data, but fails on GT servers
    perhaps has something to do with iframe?!?!

    Check what semester options are available

    Compare to previous options if pickle file available

    :param browser: selenium webdriver object
    :param verbose: flag for verbose print statements
    :param pkl: flag controlling if current read stored in pkl file
    :param email_diffs: flag to control emailing about changes found
    :return: success
    """
    logger.debug("Checking for semester options")
    browser = _lookup_classes(browser)
    # browser.switch_to.default_content()
    # browser.switch_to.frame("the_iframe")
    # select = Select(browser.find_element_by_name('term_in'))
    select = Select(browser.find_element_by_xpath(f"//select[@name='term_in']"))
    options = select.options
    otext_l = [opt.text for opt in options]
    ovalues_l = [opt.get_attribute("value") for opt in options]
    otext_s = set(otext_l)
    ovalues_s = set(ovalues_l)
    if verbose:
        print("Semester options:")
        print(f"text:\n{otext_l}")
        print(f"values:\n{ovalues_l}")
    # If possible, compare current values with previous values
    if len(otext_l) != len(otext_s):
        logger.warning("Warning: duplicate elements in option text list")
    if len(ovalues_l) != len(ovalues_s):
        logger.warning("Warning: duplicate elements in option values list")
    check_text = True
    check_values = True
    try:
        old_text = pickle.load(open("semester_text_set.p", "rb"))
    except FileNotFoundError:
        check_text = False
        logger.info("No prev semester text found")
    try:
        old_values = pickle.load(open("semester_values_set.p", "rb"))
    except FileNotFoundError:
        check_values = False
        logger.info("No prev semester values found")
    if check_text is True:
        new_text = otext_s - old_text
        dropped_text = old_text - otext_s
        if len(new_text) > 0:
            logger.info("New text:\n{new_text}")

        else:
            logger.info("No new text elements")
        if len(dropped_text) > 0:
            logger.info(f"Dropped text:\n{dropped_text}")
        else:
            logger.info("No dropped text elements")
    if check_values is True:
        new_values = ovalues_s - old_values
        dropped_values = old_values - ovalues_s
        if len(new_values) > 0:
            logger.info(f"New values:\n{new_values}")
        else:
            logger.info("No new value elements")
        if len(dropped_text) > 0:
            logger.info(f"Dropped values:\n{dropped_values}")
        else:
            logger.info("No dropped value elements")
    if email_diffs:
        if len(new_text) > 0 or len(new_values) > 0:
            subject = "New semester fields added to OSCAR"
            body = f"""\
            New text:{new_text}
            New values:{new_values}
            All text:
            {otext_s}
            All values:
            {ovalues_s}\
            """
            body = dedent(body)
            send_email(subject, body)
    if pkl:
        pickle.dump(otext_s, open("semester_text_set.p", "wb"))
        pickle.dump(ovalues_s, open("semester_values_set.p", "wb"))


def gotosem(browser, semester):
    """
    Navigate to the semester of interest

    Select 'semester' -> Advanced View -> Computer Science -> Online courses

    TBD:
    Add test to ensure user is already logged in when this is called
    Add check if the semester options change

    :param browser: Selenium webdriver object
    :param semester: Semester option value on webpage
    """
    _lookup_classes(browser)

    # Select semester
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


def scrape_courses(browser):
    """
    Scrape data from the table of courses

    Assumes browser is already pointing at the page we want to scrape.

    TBD - add check that current page is the one wanted
    May also need to add iframe check

    :param browser: Selenium webdriver object
    """
    # Scrape table
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
    logger.debug("Scrape complete")
    return rows


def dbadd(rows, scrape_time, dbname='OMSCS_CA.db'):
    """
    Creates/adds to course table & table for each course

    Known legal row sizes:
    22 if registration closed/unavailable
    26 if registration open

    :param rows: Rows from course table - returned by scrape_courses function
    :param scrape_time: Time the rows were scraped, datetime object
    :param dbname: Name of the database to write to
    """
    # Account for courses that can be registered for
    for i in range(0, len(rows)):
        if len(rows[i]) == 26:
            rows[i] = rows[i][4:]
    row_size = 22
    ue_rows = [row for row in rows[1:] if len(row) != row_size]
    if len(ue_rows) != 0:
        logger.error(f"Bad row lengths found:{len(ue_rows)}")
        logger.error(f"Rows\n{ue_rows}")

    # Table layout could change within rows of len 22 and 26
    # Ensure at minimum, key fields can be repd as int
    irows = [[row[2]] + [row[4]] + row[12:18] for row in rows[2:]]
    try:
        [int(el) for row in irows for el in row]
    except ValueError:
        logger.exception("Non integers found where expected in course table")
        # Email may not send correctly here. Needs verification.
        subject = "Non integers would in course table"
        body = f"""\
        Execution should halt for db preservation
        Rows:{rows}
        """
        body = dedent(body)
        send_email(subject, body)
        raise  # This should be a fatal error to keep db clean

    # Build Table
    # conn = sqlite3.connect(':memory:', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    conn = sqlite3.connect(dbname, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cursor = conn.cursor()
    courses = [row[2] for row in rows[2:]]
    semester_prefix = "F18"
    course_tbl = f"courses{semester_prefix}"
    # Sanitize table name. May be useful when semester_prefix is taken as arg
    if not course_tbl.isalnum():
        logger.error(f"Illegal source table name: {course_tbl}")
        exit()
    tb_exists = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{course_tbl}'"
    if not cursor.execute(tb_exists).fetchone():
        # Create table if it does not already exist
        logger.warning(f"{course_tbl} table being created")
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
            tbl_data = cursor.fetchall()
            if row_data not in tbl_data:
                logger.warning("Changes to course table rows")
                logger.warning(f"scrape: {row_data}")
                logger.warning(f"db:     {tbl_data}")
                # log differences:
                # UNTESTED
                # for i in range(0,len(row_data)):
                #     if row_data[i] != tbl_data[i]:
                #         logger.warning(f"{tbl_data[i]} -> {row_data[i]}")
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
    # Also some assurance of legal table names
    # Currently ensures starting with letter as tables cannot start with number
    # Testcase TBD
    for course in courses:
        if re.match('^[a-zA-Z][\w]+$', course):
            logger.error(f"Illegal course name found: {course}")
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
            logger.warning(f"{course} table being created")
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
    logger.debug("DB fill finished")


if __name__ == "__main__":
    print("These aren't the droids you're looking for")
