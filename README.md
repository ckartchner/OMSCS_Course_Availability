# OMSCS_Course_Availability

## Overview
Run this script to be automatically taken to the Course Availaiblity page most relevant to OMSCS students.

At GT, getting to the course availability page can be annoying, especially if you find yourself doing it repeatedly.
When I recently didn't manage to get online during the first day of registration this I found myself unable to register for the courses I wanted. As a result I found myself checking course availability very frequently waiting to pounce when more seats were made available. 

This script automates that process. 

Takes your username and password as CLI args. Necessary DUO login actions should be handled separately.
Example:
python OMSCS_course_availability.py username password

## Requirements
0) Python
1) selenium installed for Python
2) [geckodriver](https://github.com/mozilla/geckodriver/releases) for Firefox

Using other browsers should work as well, but the [appropriate driver](https://seleniumhq.github.io/docs/wd.html#quick_reference) will be needed. 
Additionally, the line identifying the browser will also need to be edited: "browser = webdriver.Firefox()"

## Notes
Semester selection is currenly hardcoded to Fall 2018. Update TBD.  
Ideally it would be preferable if a login wasn't needed to access these pages. Are you listening GT?
