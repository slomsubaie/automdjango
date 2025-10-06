import time
import pytest
from automdjango.srcode.pages.main_page import MainPage
from automdjango.srcode.drivers.driverpreparation import DriverPreparation


@pytest.fixture
def driver():
    """Fixture to initialize and quit WebDriver"""
    wd = DriverPreparation()  # get driver instance from your class
    yield wd
    wd.quit()


class Test_examine:

    def test_main_program(self, driver):
        time.sleep(10)

        flan = MainPage(driver)

        time.sleep(5)
        flan.getQueryField()
        time.sleep(5)
        actual_page_title = driver.get_page_title()
        expected_page_title = "java"
        time.sleep(2)
        print("I will try to assert what you want")
        assert expected_page_title in actual_page_title
        print("I will sleep now for 5 seconds")
        time.sleep(5)
