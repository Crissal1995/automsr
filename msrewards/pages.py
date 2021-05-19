import logging
import time
from abc import ABC

from selenium.common import exceptions
from selenium.webdriver import Remote as WebDriver
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger(__name__)


class Page(ABC):
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.driver.switch_to.window(self.driver.window_handles[-1])
        time.sleep(0.5)

    def complete(self):
        raise NotImplementedError


class BannerCookiePage(Page):
    def complete(self):
        selector = "#wcpConsentBannerCtrl > div > button"
        self.driver.find_element_by_css_selector(selector).click()


class CookieAcceptPage(Page):
    def complete(self):
        selector = "#bnp_btn_accept"
        self.driver.find_element_by_css_selector(selector).click()


class TryMicrosoftBrowserPage(Page):
    def complete(self):
        try:
            self.driver.find_element_by_id("bnp_hfly_cta2").click()
            logger.info("Dismiss 'try another browser' span")
        except exceptions.WebDriverException:
            logger.info("No 'try another browser' span found")


class LoginPage(Page):
    def __init__(self, driver, login_url: str, credentials: dict):
        super().__init__(driver=driver)
        self.login_url = login_url
        self.credentials = credentials

    def complete(self):
        url = self.driver.current_url
        if self.login_url not in url:
            logger.warning("Weren't inside a login page, exit...")
            return
        else:
            self.fill_email()
            time.sleep(0.5)
            self.fill_password()

    def select_login(self):
        selector = "body > div.simpleSignIn > div.signInOptions > span > a"
        self.driver.find_element_by_css_selector(selector).click()

    def fill_email(self):
        email = self.credentials["email"]
        self.driver.find_element_by_tag_name("input").send_keys(email)
        time.sleep(0.5)
        self.driver.find_element_by_tag_name("input").send_keys(Keys.ENTER)

    def fill_password(self):
        psw_selector = "#i0118"
        # psw_selector = "input[type=password]"
        psw = self.credentials["password"]
        self.driver.find_element_by_css_selector(psw_selector).send_keys(psw)
        time.sleep(0.5)
        self.driver.find_element_by_css_selector(psw_selector).send_keys(Keys.ENTER)


class BingLoginPage(LoginPage):
    def __init__(self, driver, login_url: str, credentials: dict, is_mobile: bool):
        super().__init__(driver, login_url, credentials)
        self.is_mobile = is_mobile

    def complete(self):
        if not self.is_mobile:
            self.driver.find_element_by_css_selector("#id_a").click()
        else:
            hamburger = "#mHamburger"
            self.driver.find_element_by_css_selector(hamburger).click()
            self.driver.find_element_by_css_selector("#hb_s").click()

        try:
            super().complete()
            logger.warning("Bing login required another login")
        except exceptions.WebDriverException:
            logger.info("No additional login was required")
