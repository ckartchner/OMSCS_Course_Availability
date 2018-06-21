from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait  # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC  # available since 2.26.0
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import sys


def main():
    """
    This script assists with loginning in and takes the user
    directly to the course availability page.relevant to OMSCS students
    """
    #
    # alternative to using argv, input userid and password here
    # userid = "username"
    # pwd = "password"
    userid = sys.argv[1]
    pwd = sys.argv[2]

    browser = webdriver.Firefox()
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

    # Neither by link or by partial link work here.... why?
    # browser.find_element_by_link_text("Student").click()
    # browser.find_element_by_partial_link_text("Student").click()
    browser.find_element_by_xpath(".//a[contains(text(), 'Student')]").click()
    # ditto above comment
    # browser.find_element_by_link_text("Look Up Classes").click()
    browser.find_element_by_xpath(".//a[contains(text(), 'Look Up Classes')]"). click()

    # Since the iframe is a separate HTML document embedded in the current one,
    # it is very important to switch to the relevant iframe
    browser.switch_to.frame("the_iframe")

    # TBD add a check here if the options change
    # XPath is the language used to locate nodes in an XML doc
    # Also add a method to easily change semesters
    # Select Fall 2018, Advanced View, Computer Science, Online courses
    browser.find_element_by_xpath("//option[@value='201808']").click()  # Select Fall
    browser.find_element_by_xpath("//input[@value='Submit']").click()  # Submit semester selection
    browser.find_element_by_xpath("(//input[@name='SUB_BTN'])[2]").click()  # Perform Advanced Search
    browser.find_element_by_xpath("//option[@value='CS']").click()  # Select Computer Science Department
    select = Select(browser.find_element_by_id("camp_id"))  # Select Campus
    select.deselect_all()  # If this isn't done, multiple items are selected
    select.select_by_value('O')  # Select only online options
    # browser.find_element_by_xpath("(//option[@value='0'])[2]").click()
    browser.find_element_by_name("SUB_BTN").click()


if __name__ == "__main__":
    # execute only if run as a script
    if len(sys.argv) != 3:
        print("Invalid number of script arguments")
        print("Requires 'username' and 'password' as arguments")
        print("EG: python OMSCS_course_availability.py username password")
        print("Please try again.")
        exit()
    main()
