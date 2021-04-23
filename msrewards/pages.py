import logging
import time
from abc import ABC

from selenium.common import exceptions
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger(__name__)


class Page(ABC):
    def __init__(self, rewards):
        self.rewards = rewards
        self.driver = rewards.driver
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


class BingLoginPage(Page):
    def complete(self):
        if not self.rewards.is_mobile:
            self.driver.find_element_by_css_selector("#id_a").click()
        else:
            hamburger = "#mHamburger"
            self.driver.find_element_by_css_selector(hamburger).click()
            self.driver.find_element_by_css_selector("#hb_s").click()

        try:
            LoginPage(self.rewards).complete()
            logger.warning("Bing login required another login")
        except exceptions.WebDriverException:
            logger.info("No additional login was required")


class LoginPage(Page):
    def complete(self):
        url = self.driver.current_url
        if self.rewards.login_url not in url:
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
        email = self.rewards.credentials["email"]
        self.driver.find_element_by_tag_name("input").send_keys(email)
        time.sleep(0.5)
        self.driver.find_element_by_tag_name("input").send_keys(Keys.ENTER)

    def fill_password(self):
        # psw_selector = "#i0118"
        psw_selector = "input[type=password]"
        psw = self.rewards.credentials["password"]
        self.driver.find_element_by_css_selector(psw_selector).send_keys(psw)
        time.sleep(0.5)
        self.driver.find_element_by_css_selector(psw_selector).send_keys(Keys.ENTER)
