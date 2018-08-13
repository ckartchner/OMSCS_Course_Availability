
# OMSCS_Course_Availability

Scripts to make navigating OSCAR registration easier

## File overview
- coursexp.py - Course Explorer - library used to interact with OSCAR
- etracker.py - Enrollment Tracker - Stores enrollment info in a database for later reference
- regpage.py - Navigate directly to registration page. It doesn't get much faster than this.

## Environment variable setup

To use the scripts, at minimum your GT username and password will need to be supplied.
To prevent putting your id/password in your history and to avoid accidentally commiting
them to git these scripts expect the use of an environment variables file.
Necessary DUO login actions still need to be handled separately.

To setup the .env file:
1) In the same directory as your OMSCS_course_availability.py,
open a .env with your favorite editor
```
vim .env
```

2) Add your login info to the file
```
OMS_ID=yourUserName
OMS_PWD=yourPassword
```

3) Save

Additionally, etracker currently expects the following in the .env file:
- EMAIL_PWD - password for smtp server login
- EMAIL_USER - username for smtp server login
- TO_EMAIL - email address messages should go to
- FROM_EMAIL - email address messages should be reported as from


## Requirements
0) Python 3.x
1) selenium installed for Python
2) [geckodriver](https://github.com/mozilla/geckodriver/releases) for Firefox
3) python-dotenv
4) lxml

Using other browsers should work as well, but the [appropriate driver](https://seleniumhq.github.io/docs/wd.html#quick_reference) will be needed.
Additionally, the line identifying the browser will also need to be edited:
"browser = webdriver.Firefox()"
