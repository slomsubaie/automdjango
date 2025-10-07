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
from automdjango.srcode.custom_exceptions.unsupported_browser_exception import UnsupportedBrowserException
from propertiesloader import PropertiesLoader
try:
    from selenium_stealth import stealth
except Exception:  # ImportError or other runtime import issues
    stealth = None
    logging.getLogger(__name__).warning(
        "selenium-stealth not available; proceeding without it. Rebuild container to install."
    )

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

os.environ["SELENIUM_CACHE"] = tempfile.mkdtemp()

class DriverPreparation:
    def __init__(self):
        logging.info("🔧 Initializing WebDriver...")
        self.propLoader = PropertiesLoader()
        self.user_data_dir = None
        self.driver = None

        browser = self.propLoader.getBrowserName().lower()
        if browser == "chrome":
            self.__initializeChromeDriver()
        else:
            raise UnsupportedBrowserException(browser)

        self.driver.get(self.propLoader.getWebsite())
        # Optionally try to solve reCAPTCHA if present and enabled
        try:
            if os.environ.get("ENABLE_RECAPTCHA_SOLVER", "0") in ("1", "true", "True", "yes"):
                from automdjango.srcode.utils.recaptcha_solver import try_solve_recaptcha_if_present
                try_solve_recaptcha_if_present(self.driver)
        except Exception as e:
            logging.warning(f"⚠️ reCAPTCHA solver skipped or failed: {e}")

    def __generate_unique_dir(self):
        return os.path.join("/tmp", f"chrome_profile_{uuid.uuid4()}")

    def __chromeOptionsPreparation(self) -> Options:
        options = webdriver.ChromeOptions()
        persistent_profile = os.environ.get("USER_DATA_DIR")
        self.user_data_dir = persistent_profile if persistent_profile else self.__generate_unique_dir()

        chrome_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-extensions",
            f"--user-data-dir={self.user_data_dir}",
            "--disable-software-rasterizer",
            "--window-size=1366,768",
            "--lang=en-US,en;q=0.9",
        ]
        if os.environ.get("INCOGNITO", "0") in ("1", "true", "True", "yes"):
            chrome_args.append("--incognito")

        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option(
            "prefs",
            {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "intl.accept_languages": "en-US,en",
            },
        )

        for arg in chrome_args:
            options.add_argument(arg)

        if os.environ.get("CHROME_BIN"):
            options.add_argument("--headless=new")
            options.binary_location = os.environ["CHROME_BIN"]

        logging.info(f"ℹ️ Chrome options prepared (user data dir: {self.user_data_dir})")
        return options

    def __initializeChromeDriver(self):
        chrome_options = self.__chromeOptionsPreparation()
        selenium_remote_url = os.environ.get("SELENIUM_REMOTE_URL")
        try:
            if selenium_remote_url:
                # Use remote Selenium service (e.g., compose service `selenium`)
                self.driver = webdriver.Remote(command_executor=selenium_remote_url, options=chrome_options)
                logging.info(f"✅ Remote Chrome WebDriver started at {selenium_remote_url}")
            else:
                chromedriver_path = ChromeDriverManager().install()
                self.driver = webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)
                logging.info("✅ Local Chrome WebDriver started successfully")
            # Apply anti-automation stealth tweaks only if explicitly enabled
            if os.environ.get("ENABLE_STEALTH", "0") in ("1", "true", "True", "yes"):
                self.__applyAntiAutomationStealth()
                # Apply selenium-stealth (best-effort)
                if stealth is not None:
                    try:
                        stealth(
                            self.driver,
                            languages=["en-US", "en"],
                            vendor="Google Inc.",
                            platform="Win32",
                            webgl_vendor="Intel Inc.",
                            renderer="Intel Iris OpenGL Engine",
                            fix_hairline=True,
                        )
                    except Exception as e:
                        logging.warning(f"⚠️ selenium-stealth could not be applied: {e}")
        except WebDriverException as e:
            logging.error(f"❌ Failed to start Chrome WebDriver: {e}")
            raise

    def __applyAntiAutomationStealth(self):
        """Reduce obvious automation signals that often trigger reCAPTCHA on Google props."""
        try:
            # Enable Network domain to set headers
            try:
                self.driver.execute_cdp_cmd("Network.enable", {})
            except Exception:
                pass

            # Set a realistic desktop Chrome user agent via CDP
            realistic_ua = os.environ.get(
                "REALISTIC_UA",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            )
            try:
                self.driver.execute_cdp_cmd(
                    "Network.setUserAgentOverride",
                    {"userAgent": realistic_ua, "platform": "Windows"},
                )
            except Exception:
                # CDP might not be available in some environments; continue best-effort
                pass

            # Accept-Language header alignment (optional)
            if os.environ.get("SET_ACCEPT_LANGUAGE", "1") in ("1", "true", "True", "yes"):
                try:
                    self.driver.execute_cdp_cmd(
                        "Network.setExtraHTTPHeaders",
                        {"headers": {"Accept-Language": os.environ.get("ACCEPT_LANGUAGE", "en-US,en;q=0.9")}},
                    )
                except Exception:
                    pass

            # Timezone override if explicitly configured
            tz = os.environ.get("TZ_OVERRIDE")
            if tz:
                try:
                    self.driver.execute_cdp_cmd(
                        "Emulation.setTimezoneOverride",
                        {"timezoneId": tz},
                    )
                except Exception:
                    pass

            # Hide webdriver and spoof a few common properties before any page scripts run
            stealth_script = """
                // Pass the Languages Test
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                
                // Pass the Plugins Length Test
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                
                // Pass the Webdriver Test
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                
                // Pass the Chrome Test
                window.chrome = window.chrome || { runtime: {} };
                
                // Pass the Permissions Test
                const originalQuery = window.navigator.permissions && window.navigator.permissions.query;
                if (originalQuery) {
                  window.navigator.permissions.query = (parameters) => (
                    parameters && parameters.name === 'notifications' ?
                      Promise.resolve({ state: Notification.permission }) :
                      originalQuery(parameters)
                  );
                }

                // Hardware concurrency spoof (default 8, can be overridden by setting window.__STEALTH_CORES__ earlier)
                try {
                  const cores = parseInt(window.__STEALTH_CORES__) || 8;
                  Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => cores });
                } catch (e) {}

                // Platform and vendor
                Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
                Object.defineProperty(navigator, 'vendor', { get: () => 'Google Inc.' });

                // WebGL vendor/renderer spoof
                try {
                  const getParameter = WebGLRenderingContext.prototype.getParameter;
                  WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) return (window.__STEALTH_WEBGL_VENDOR__ || 'Intel Inc.'); // UNMASKED_VENDOR_WEBGL
                    if (parameter === 37446) return (window.__STEALTH_WEBGL_RENDERER__ || 'Intel Iris OpenGL Engine'); // UNMASKED_RENDERER_WEBGL
                    return getParameter.call(this, parameter);
                  };
                } catch (e) {}
            """
            try:
                self.driver.execute_cdp_cmd(
                    "Page.addScriptToEvaluateOnNewDocument", {"source": stealth_script}
                )
            except Exception:
                pass
        except Exception as e:
            logging.warning(f"⚠️ Stealth tweaks could not be fully applied: {e}")

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

    def click_on_element(self, element: WebElement):
        logging.info(f"🖱️ Clicking element {element}")
        element.click()

    def get_page_title(self) -> str:
        return self.driver.title

