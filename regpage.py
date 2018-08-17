"""Navigate directly to the registration page for the supplied semester"""
from coursexp import gtlogin, gotosem, browser_setup

# Setup optional logging
import logging
from coursexp import logsetup
logger = logging.getLogger(__name__)
logger = logsetup(logger)

# Navigate to page
browser = browser_setup(headless=False)
gtlogin(browser)
semester = '201808'
gotosem(browser, semester)
exit()
