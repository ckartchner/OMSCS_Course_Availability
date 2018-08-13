"""
Enrollment tracker

Records enrollment changes over time
"""
from apscheduler.schedulers.blocking import BlockingScheduler
import datetime
import logging
from coursexp import browser_setup, gtlogin, gotosem, scrape_courses, dbadd

# Need to do something about the scope here?
logging.basicConfig(
    filename='OMSCS_CA.log',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.DEBUG)


def scheduled_actions(browser, semester):
    """
    Actions taken repeatedly to generate time series

    Concern:
    Potential remains for unhandled exceptions if resources unavailable

    :param browser: Selenium browser object
    :param semester: Semester used in gotosem navigation
    """
    ct = datetime.datetime.now()
    print(f"Taking scheduled action {ct}")
    logging.debug(f"Preforming scheduled actions on {semester}")
    gtlogin(browser)
    gotosem(browser, semester)
    rows = scrape_courses(browser)
    scrape_time = datetime.datetime.now()
    dbadd(rows, scrape_time)


def coordinator(semester='201808'):
    """
    Coordinates initial setup, then schedules repeated actions of scraper

    :param semester: Semester used in gotosem navigation
    """
    logging.debug("Running main code")
    browser = browser_setup(headless=False)
    scheduler = BlockingScheduler()
    scheduler.add_job(scheduled_actions,
                      args=[browser, semester],
                      trigger='interval',
                      minutes=30,
                      next_run_time=datetime.datetime.now())
    try:
        print("Starting scheduler")
        print('Press Ctrl+C to exit')
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    coordinator()
