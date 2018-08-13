"""Navigate directly to the registration page for the supplied semester"""

from coursexp import gtlogin, gotosem, browser_setup

browser = browser_setup(headless=False)
gtlogin(browser)
semester = '201808'
gotosem(browser, semester)
exit()
