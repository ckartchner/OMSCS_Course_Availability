"""
Enrollment tracker

Records enrollment changes over time
"""
from apscheduler.schedulers.blocking import BlockingScheduler
import datetime
import logging
from coursexp import browser_setup, gtlogin, gotosem, scrape_courses, dbadd, logsetup

logger = logging.getLogger(__name__)
logger = logsetup(logger)


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
    logger.info(f"Preforming scheduled actions on {semester}")
    gtlogin(browser)
    gotosem(browser, semester)
    rows = scrape_courses(browser)
    scrape_time = datetime.datetime.now()
    dbadd(rows, scrape_time)


def coordinator(semester='201902'):
    """
    Coordinates initial setup, then schedules repeated actions of scraper

    :param semester: Semester used in gotosem navigation
    """
    logger.debug("Starting the coordinator")
    browser = browser_setup(headless=True)
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
    # TODO add argparse:
    # Args: headless, semester
    coordinator()
