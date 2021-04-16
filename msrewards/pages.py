import time
from abc import ABC

from selenium.webdriver.remote.webdriver import WebDriver


class Page(ABC):
    def __init__(self, driver: WebDriver):
        self.driver = driver
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
    def __init__(self, driver: WebDriver, is_mobile: bool):
        super(BingLoginPage, self).__init__(driver)
        self.is_mobile = is_mobile

    def complete(self):
        if not self.is_mobile:
            self.driver.find_element_by_name("submit").click()
        else:
            hamburger = "#mHamburger"
            self.driver.find_element_by_css_selector(hamburger).click()
            self.driver.find_element_by_css_selector("#hb_s").click()


class LoginPage(Page):
    def __init__(self, driver: WebDriver, credentials: dict):
        super().__init__(driver)
        self.credentials = credentials

    def complete(self):
        # self.select_login()
        time.sleep(2)
        self.fill_email()
        self.fill_password()

    def select_login(self):
        selector = "body > div.simpleSignIn > div.signInOptions > span > a"
        self.driver.find_element_by_css_selector(selector).click()

    def fill_email(self):
        email_selector = "#i0116"
        email = self.credentials["email"]

        field = self.driver.find_element_by_css_selector(email_selector)
        self.driver.execute_script(f"arguments[0].value='{email}'", field)

        forward_selector = "#idSIButton9"
        self.driver.find_element_by_css_selector(forward_selector).click()

    def fill_password(self):
        time.sleep(10)
        psw_selector = "#i0118"
        psw = self.credentials["password"]

        # self.driver.find_element_by_css_selector(psw_selector).send_keys(psw)

        field = None
        while not field:
            field = self.driver.find_element_by_css_selector(psw_selector)
        self.driver.execute_script(f"arguments[0].value='{psw}'", field)

        remain_logged_sel = "#idChkBx_PWD_KMSI0Pwd"
        time.sleep(2)
        self.driver.find_element_by_css_selector(remain_logged_sel).click()

        forward_selector = "#idSIButton9"
        self.driver.find_element_by_css_selector(forward_selector).click()
