from selenium import webdriver

def browser_setup(browser="Firefox", headless=True):
    """
    General browser config

    :param headless: Set if headless mode is to be used with the browser
    """
    if browser == "Firefox":
        from selenium.webdriver.firefox.options import Options
        options = Options()
        options.headless = headless
        browser = webdriver.Firefox(firefox_options=options)
    elif browser == "Chrome":
        from selenium.webdriver.chrome.options import Options
        options = Options()
        options.headless = headless
        options.add_experimental_option("detach", True)  # Keeps Chrome window open after script terminates
        browser = webdriver.Chrome(chrome_options=options)
    else:
        print("Unsupported browser type")
        raise ValueError
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