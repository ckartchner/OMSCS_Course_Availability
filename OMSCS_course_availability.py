from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait  # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC  # available since 2.26.0
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from dotenv import load_dotenv  # installed with 'pip install python-dotenv'
from lxml import html
import sys
import os
import unicodedata
import logging

import pickle
import time
import datetime

def setup_logging():
    logging.basicConfig(
            filename='OMSCS_CA.log',
            format='%(asctime)s %(levelname)-8s %(message)s',
            level=logging.DEBUG)

def browser_setup():
    """
    General browser config
    """
    # General browser config
    options = Options()
    options.set_headless(headless=False)
    browser = webdriver.Firefox(firefox_options=options)

    # #Load cookies ... doesn't help bypass the need for a push
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

def gt_login(browser):
    auto_push = False
    logging.debug('Opening login page')
    browser.implicitly_wait(15)  # wait 15 seconds for any field to appear
    browser.get("https://buzzport.gatech.edu/cp/home/displaylogin")
    browser.find_element_by_id("login_btn").click()

    # Login if not already logged in.
    # Note: Not yet able to bypass login
    try:
        browser.find_element_by_id("username").clear()
        browser.find_element_by_id("username").send_keys(userid)
        browser.find_element_by_id("password").clear()
        browser.find_element_by_id("password").send_keys(pwd)
        browser.find_element_by_name("submit").click()
        logging.debug("Password submission path taken")
    except NoSuchElementException:
        logging.debug("It appears you were already authenticated")

    if auto_push == False:
        # Ensures remember me for 7 days is selected when push gets sent
        # Doesn't seem to matter though... login info save between sessions not yet working.
        WebDriverWait(browser, 10).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "duo_iframe")))
        # Select "Remember me for 7 days"
        WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.NAME, "dampen_choice")))
        browser.find_element_by_name("dampen_choice").click()
        # Send Push
        WebDriverWait(browser,10).until(EC.element_to_be_clickable((By.XPATH, ".//button[contains(text(), 'Send Me a Push')]")))
        browser.find_element_by_xpath(".//button[contains(text(), 'Send Me a Push')]").click()
        # Without switching out of the iframe, a "Can't access dead object" error will be thrown with next find attempt
        browser.switch_to.default_content()
        logging.debug("Duo request sent to phone")


    # Long variable delay here due to waiting for duo authentication
    # timeout in seconds
    WebDriverWait(browser, 120).until(EC.title_is("BuzzPort"))
    # Store login cookies
    # pickle.dump(browser.get_cookies(), open("cookies.pkl", "wb"))

    browser.find_element_by_xpath(".//a[contains(text(), 'Student')]").click()

def scrape_courses(browser, semester):
    # TBD... add link to main buzzport page so this can be recalled
    # Route selection
    # There are multiple routes to get to the course availability
    # The path flag is used to switch the route used.
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
        timestamp = str(datetime.datetime.now())
        browser.save_screenshot(f'screenshot_OSCAR_attempt_{timestamp}.png')
    # XPath is the language used to locate nodes in an XML doc

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
    # browser.switch_to.frame("the_iframe")
    html_source = browser.page_source
    parsed = html.fromstring(html_source)
    # Subelements selected below:
    # [0] - tbody
    # [1] - "Sections Found"
    course_table = parsed.xpath('//table[@class="datadisplaytable"]')[0][1]

    # The first element of the table is the "Computer Science" section
    # Second element is the row labeling the columns
    # All remaining elements are rows for each course
    # unicode normalize removes \xa0 and any other potentially odd unicode surprises
    rows = [unicodedata.normalize("NFKD", a.text_content()).split('\n') for a in course_table]
    return rows

def main(userid, pwd, semester='201808'):
    """
    This script assists with logging in and takes the user
    directly to the course availability page.relevant to OMSCS students
    """
    setup_logging()
    browser = browser_setup()
    gt_login(browser)
    rows = scrape_courses(browser, semester)

    # Print all rows:
    print(*rows, sep='\n')

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


if __name__ == "__main__":
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
        main(userid, pwd)
    elif len(sys.argv) == 3:
        # Actions if username and password supplied as CLI arguments
        userid = sys.argv[1]
        pwd = sys.argv[2]
        main(userid, pwd)
