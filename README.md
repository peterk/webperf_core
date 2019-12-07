# Webperf Core
Minimalistic client mainly running on PythonAnywhere.com, accessing different websites, or web-APIs, and scraping them.

## Dependencies
Not found in the standard lib:

* Flask
* flask_sqlalchemy
* sqlalchemy
* requests
* BeautifulSoup 4

Also need some MySQL stuff, but which libs differ on Macos and Linux. On PythonAnywhere.com it worked without any effort.

## Usage
Open the terminal, enter folder and type 'python default.py'
Also support arguments, 'python default.py id=1' to only test site with id 1.
