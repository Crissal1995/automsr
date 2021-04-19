import time
from abc import ABC

from selenium.webdriver.common.keys import Keys

from msrewards.rewards import MicrosoftRewards


class Page(ABC):
    def __init__(self, rewards: MicrosoftRewards):
        self.rewards = rewards
        self.driver = rewards.driver
        self.driver.switch_to.window(self.driver.window_handles[-1])

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
            self.driver.find_element_by_name("submit").click()
        else:
            hamburger = "#mHamburger"
            self.driver.find_element_by_css_selector(hamburger).click()
            self.driver.find_element_by_css_selector("#hb_s").click()


class LoginPage(Page):
    def complete(self):
        # self.select_login()
        time.sleep(2)
        self.fill_email()
        self.fill_password()

    def select_login(self):
        selector = "body > div.simpleSignIn > div.signInOptions > span > a"
        self.driver.find_element_by_css_selector(selector).click()

    def fill_email(self):
        email = self.rewards.credentials["email"]
        input_field = self.driver.find_element_by_tag_name("input")
        input_field.send_keys(email)
        input_field.send_keys(Keys.ENTER)

    def fill_password(self):
        # psw_selector = "#i0118"
        psw_selector = "input[type=password]"
        psw = self.rewards.credentials["password"]
        psw_field = self.driver.find_element_by_css_selector(psw_selector)
        psw_field.send_keys(psw)
        psw_field.send_keys(Keys.ENTER)
