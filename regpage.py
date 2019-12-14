"""Navigate directly to the registration page for the supplied semester"""
from coursexp import gtlogin, gotosem
from browser_setup import browser_setup
import argparse
# Setup optional logging
import logging
from coursexp import logsetup
logger = logging.getLogger(__name__)
logger = logsetup(logger)


def goto_page(browser_type: str, headless: bool, semester: str) -> None:
    """
    Navigate to
    :param browser_type: Browser type to use
    :param headless: Indicator if browser should run in headless mode
    :return: None
    """
    browser = browser_setup(browser=browser_type, headless=headless)
    gtlogin(browser, auto_push=True)
    gotosem(browser, semester)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--browser",
                        type=str,
                        help="Which browser type to use. Supported types: Firefox, Chrome. Default:Firefox",
                        default="Firefox")
    parser.add_argument("--headless",
                        type=str,
                        help="Boolean indicating if browser should run in headless mode. Default: False",
                        default="False")
    parser.add_argument("-s", "--semester",
                        type=str,
                        help="Semester to check. Default: 201902",
                        default="201902")
    args = parser.parse_args()
    logger.debug(f"Args: {args}")
    goto_page(args.browser, args.headless, args.semester)
