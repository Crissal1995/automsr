import json
from abc import ABC

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webdriver import WebDriver


class Page(ABC):
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def complete(self):
        raise NotImplementedError


class CookieAcceptPage(Page):
    def complete(self):
        selector = "#bnp_btn_accept"
        self.driver.find_element_by_css_selector(selector).click()


class LoginPage(Page):
    def __init__(self, driver):
        super().__init__(driver)
        with open("credentials.json") as f:
            self.credentials = json.load(f)

    def complete(self):
        try:
            self.select_login()
        except NoSuchElementException:
            pass
        self.fill_email()
        self.fill_password()

    def select_login(self):
        selector = "body > div.simpleSignIn > div.signInOptions > span > a"
        self.driver.find_element_by_css_selector(selector).click()

    def fill_email(self):
        email_selector = "#i0116"
        email = self.credentials["email"]
        self.driver.find_element_by_css_selector(email_selector).send_keys(email)

        forward_selector = "#idSIButton9"
        self.driver.find_element_by_css_selector(forward_selector).click()

    def fill_password(self):
        psw_selector = "#i0118"
        psw = self.credentials["password"]
        self.driver.find_element_by_css_selector(psw_selector).send_keys(psw)

        remain_logged_sel = "#idChkBx_PWD_KMSI0Pwd"
        self.driver.find_element_by_css_selector(remain_logged_sel).click()

        forward_selector = "#idSIButton9"
        self.driver.find_element_by_css_selector(forward_selector).click()

        self.driver.refresh()
