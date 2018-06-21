
# OMSCS_Course_Availability

## Overview
Run this script to be automatically taken to the Course Availability page most
relevant to OMSCS students.

At GT, getting to the course availability page can be annoying, especially if
you find yourself doing it repeatedly. When I recently didn't manage to get
online during the first day of registration I found myself unable to register
for the courses I wanted. Consequently, I fell under the curse of constantly
checking course the availability waiting to pounce when more seats were
made available.

This script automates that process.

To use this script, your GT username and password will need to be supplied.
This can be done by either using a .env file or running the script with your
username and password as CLI args.
Necessary DUO login actions still need to be handled separately.

Using a .env file (Recommended):
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

Using CLI args:
python OMSCS_course_availability.py username password

## Requirements
0) Python 3.x
1) selenium installed for Python
2) [geckodriver](https://github.com/mozilla/geckodriver/releases) for Firefox
3) python-dotenv

Using other browsers should work as well, but the [appropriate driver](https://seleniumhq.github.io/docs/wd.html#quick_reference) will be needed.
Additionally, the line identifying the browser will also need to be edited:
"browser = webdriver.Firefox()"

## Notes
Semester selection is currently hardcoded to Fall 2018. Update TBD.  
Ideally it would be preferable if a login wasn't needed to access these pages.
