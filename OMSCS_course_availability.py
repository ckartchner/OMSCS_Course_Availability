from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait  # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC  # available since 2.26.0
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options
from dotenv import load_dotenv  # installed with 'pip install python-dotenv'
from lxml import html
import sys
import os
import unicodedata


def main(userid, pwd):
    """
    This script assists with loginning in and takes the user
    directly to the course availability page.relevant to OMSCS students
    """
    # Route selection
    # There are multiple routes to get to the course availability
    # The path flag is used to switch the route used.
    route_to_data = 'new'

    # General browser config
    options = Options()
    options.set_headless(headless=True)
    browser = webdriver.Firefox(firefox_options=options)
    browser.implicitly_wait(15)  # wait 15 seconds for any field to appear

    browser.get("https://buzzport.gatech.edu/cp/home/displaylogin")
    browser.find_element_by_id("login_btn").click()
    # Login if not already logged in.
    # Note: Not yet validated running if already logged in.
    try:
        browser.find_element_by_id("username").clear()
        browser.find_element_by_id("username").send_keys(userid)
        browser.find_element_by_id("password").clear()
        browser.find_element_by_id("password").send_keys(pwd)
        browser.find_element_by_name("submit").click()
    except NoSuchElementException:
        print("It appears you are already authenticated")

    # Long variable delay here due to waiting for duo authentication
    # timeout in seconds
    WebDriverWait(browser, 120).until(EC.title_is("BuzzPort"))

    browser.find_element_by_xpath(".//a[contains(text(), 'Student')]").click()
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

    # XPath is the language used to locate nodes in an XML doc

    # Select Fall 2018, Advanced View, Computer Science, Online courses
    # TBD(1): add check here if the options change
    # TBD(2): add method to easily change semesters

    # Select Fall
    browser.find_element_by_xpath("//option[@value='201808']").click()
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
