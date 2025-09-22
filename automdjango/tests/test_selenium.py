from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
# add headless if you want: chrome_options.add_argument("--headless=new")

driver = webdriver.Remote(
    command_executor="http://selenium:4444/wd/hub",
    options=chrome_options,
)
