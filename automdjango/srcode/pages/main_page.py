from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from automdjango.srcode.drivers.driverpreparation import DriverPreparation
import time

class MainPage:

    searchDiv = (By.ID, "APjFqb")
    searchQuery = "java"


    def __init__(self, driver: DriverPreparation):
        print("I'm in init method in main page class")
        self.driver = driver

    def getQueryField(self):
        try:
            print("I'm in queryField method")
            popupCloseButton = self.driver.find_element(MainPage.searchDiv)
            print("I found the element")
            print("I will send the query to the element")
            time.sleep(3)
            popupCloseButton.send_keys(self.searchQuery)
            time.sleep(3)
            print("I will click on the element")
            popupCloseButton.send_keys(Keys.RETURN)
        except NoSuchElementException:
            print("popupCloseButton is not found")
