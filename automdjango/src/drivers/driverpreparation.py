import os
import tempfile
import uuid
import shutil
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webelement import WebElement
from selenium.common import NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from automdjango.src.custom_exceptions import unsupported_browser_exception
import properties_loader

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

os.environ["SELENIUM_CACHE"] = tempfile.mkdtemp()

class driver_preparation:
    def __init__(self):
        logging.info("🔧 Initializing WebDriver...")
        self.propLoader = properties_loader.properties_loader()
        self.user_data_dir = None
        self.driver = None

        browser = self.propLoader.getBrowserName().lower()
        if browser == "chrome":
            self.__initializeChromeDriver()
        elif browser == "edge":
            raise unsupported_browser_exception("Edge driver not supported in this environment")
        else:
            raise unsupported_browser_exception(browser)

        self.driver.get(self.propLoader.getWebsite())

    def __generate_unique_dir(self):
        return os.path.join("/tmp", f"chrome_profile_{uuid.uuid4()}")

    def __chromeOptionsPreparation(self) -> Options:
        options = webdriver.ChromeOptions()
        self.user_data_dir = self.__generate_unique_dir()

        chrome_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-extensions",
            f"--user-data-dir={self.user_data_dir}",
            "--remote-debugging-port=9222",
            "--disable-software-rasterizer"
        ]

        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        for arg in chrome_args:
            options.add_argument(arg)

        if os.environ.get("CHROME_BIN"):
            options.add_argument("--headless=new")
            options.binary_location = os.environ["CHROME_BIN"]

        logging.info(f"ℹ️ Chrome options prepared (user data dir: {self.user_data_dir})")
        return options

    def __initializeChromeDriver(self):
        chrome_options = self.__chromeOptionsPreparation()
        try:
            chromedriver_path = ChromeDriverManager().install()
            self.driver = webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)
            logging.info("✅ Chrome WebDriver started successfully")
        except WebDriverException as e:
            logging.error(f"❌ Failed to start Chrome WebDriver: {e}")
            raise

    def navigateTo(self, url: str):
        logging.info(f"🌍 Navigating to {url}")
        self.driver.get(url)

    def getDriver(self):
        return self.driver

    def quit(self):
        logging.info("🛑 Quitting WebDriver...")
        if self.driver:
            self.driver.quit()
        if self.user_data_dir and os.path.exists(self.user_data_dir):
            shutil.rmtree(self.user_data_dir, ignore_errors=True)

    def find_element(self, element: tuple) -> WebElement:
        try:
            return self.driver.find_element(*element)
        except NoSuchElementException:
            logging.warning(f"⚠️ Element not found: {element}")

    def clickOnElement(self, element: WebElement):
        logging.info(f"🖱️ Clicking element {element}")
        element.click()
