from requests_html import HTMLSession, HTMLResponse
from environs import Env

env = Env()
env.read_env()

session = HTMLSession()

cookies = {
    "AMCSecAuth": env("AMCSecAuth"),
    "ANON": env("ANON"),
    "NAP": env("NAP"),
}

r: HTMLResponse = session.get("https://account.microsoft.com/rewards/", cookies=cookies)

r.html.render()

print(r.status_code)
print(r.text)

"""
E:\Gitkraken\auto_msrewards\venv_temp\Scripts\python.exe C:\Users\Cristiano\AppData\Local\JetBrains\Toolbox\apps\PyCharm-P\ch-0\203.7717.81\plugins\python\helpers\pydev\pydevconsole.py --mode=client --port=5998
import sys; print('Python %s on %s' % (sys.version, sys.platform))
sys.path.extend(['E:\\Gitkraken\\auto_msrewards', 'E:/Gitkraken/auto_msrewards'])
PyDev console: starting.
Python 3.8.1 (tags/v3.8.1:1b293b6, Dec 18 2019, 23:11:46) [MSC v.1916 64 bit (AMD64)] on win32
from environs import Env
env = Env()
env.read_env()
cookies = {
    "AMCSecAuth": env("AMCSecAuth"),
    "ANON": env("ANON"),
    "NAP": env("NAP"),
}
from selenium.webdriver import Chrome
driver = Chrome
driver = Chrome()
driver.add_cookie(cookies)
Traceback (most recent call last):
  File "<input>", line 1, in <module>
  File "E:\Gitkraken\auto_msrewards\venv_temp\lib\site-packages\selenium\webdriver\remote\webdriver.py", line 894, in add_cookie
    self.execute(Command.ADD_COOKIE, {'cookie': cookie_dict})
  File "E:\Gitkraken\auto_msrewards\venv_temp\lib\site-packages\selenium\webdriver\remote\webdriver.py", line 321, in execute
    self.error_handler.check_response(response)
  File "E:\Gitkraken\auto_msrewards\venv_temp\lib\site-packages\selenium\webdriver\remote\errorhandler.py", line 242, in check_response
    raise exception_class(message, screen, stacktrace)
selenium.common.exceptions.InvalidArgumentException: Message: invalid argument: missing 'name'
  (Session info: chrome=89.0.4389.114)
for key, val in cookies.items():
    driver.add_cookie({"name": key, "value": val})
    
Traceback (most recent call last):
  File "<input>", line 2, in <module>
  File "E:\Gitkraken\auto_msrewards\venv_temp\lib\site-packages\selenium\webdriver\remote\webdriver.py", line 894, in add_cookie
    self.execute(Command.ADD_COOKIE, {'cookie': cookie_dict})
  File "E:\Gitkraken\auto_msrewards\venv_temp\lib\site-packages\selenium\webdriver\remote\webdriver.py", line 321, in execute
    self.error_handler.check_response(response)
  File "E:\Gitkraken\auto_msrewards\venv_temp\lib\site-packages\selenium\webdriver\remote\errorhandler.py", line 242, in check_response
    raise exception_class(message, screen, stacktrace)
selenium.common.exceptions.InvalidCookieDomainException: Message: invalid cookie domain
  (Session info: chrome=89.0.4389.114)
link = "https://account.microsoft.com/rewards/"
driver.get(link)
for key, val in cookies.items():
    driver.add_cookie({"name": key, "value": val})
    
driver.get(link)
import selenium
driver.find_element_by_xpath("//*[@id=\"daily-sets\"]/mee-card-group[1]/div/mee-card[1]/div/card-content/mee-rewards-daily-set-item-content/div/div[3]/a")
<selenium.webdriver.remote.webelement.WebElement (session="62a252410e16dec2bf186d0ae3422b05", element="b194096c-b21b-4832-9b56-6bb28a3686fd")>
x = driver.find_element_by_xpath("//*[@id=\"daily-sets\"]/mee-card-group[1]/div/mee-card[1]/div/card-content/mee-rewards-daily-set-item-content/div/div[3]/a")
x.click()
Traceback (most recent call last):
  File "<input>", line 1, in <module>
  File "E:\Gitkraken\auto_msrewards\venv_temp\lib\site-packages\selenium\webdriver\remote\webelement.py", line 80, in click
    self._execute(Command.CLICK_ELEMENT)
  File "E:\Gitkraken\auto_msrewards\venv_temp\lib\site-packages\selenium\webdriver\remote\webelement.py", line 633, in _execute
    return self._parent.execute(command, params)
  File "E:\Gitkraken\auto_msrewards\venv_temp\lib\site-packages\selenium\webdriver\remote\webdriver.py", line 321, in execute
    self.error_handler.check_response(response)
  File "E:\Gitkraken\auto_msrewards\venv_temp\lib\site-packages\selenium\webdriver\remote\errorhandler.py", line 242, in check_response
    raise exception_class(message, screen, stacktrace)
selenium.common.exceptions.ElementNotInteractableException: Message: element not interactable
  (Session info: chrome=89.0.4389.114)
x = '//*[@id="daily-sets"]/mee-card-group[1]/div/mee-card[1]/div/card-content/mee-rewards-daily-set-item-content/div/div[3]/a/span'
xpath = '//*[@id="daily-sets"]/mee-card-group[1]/div/mee-card[1]/div/card-content/mee-rewards-daily-set-item-content/div/div[3]/a/span'
driver.find_element_by_xpath(xpath).click()
agree_all = '//*[@id="wcpConsentBannerCtrl"]/div[2]/button[1]'
driver.find_element_by_xpath(agree_all).click()
xpath
'//*[@id="daily-sets"]/mee-card-group[1]/div/mee-card[1]/div/card-content/mee-rewards-daily-set-item-content/div/div[3]/a/span'
xpath2 = xpath
xpath2 = '//*[@id="daily-sets"]/mee-card-group[1]/div/mee-card[2]/div/card-content/mee-rewards-daily-set-item-content/div/div[3]/a/span'
driver.find_element_by_xpath(xpath2).click()
xpath2true = '//*[@id="daily-sets"]/mee-card-group[1]/div/mee-card[2]/div/card-content/mee-rewards-daily-set-item-content/div/div[3]/a/span'
xpath2 == xpath2true
True
driver.find_element_by_xpath(xpath2).click()
driver.find_element_by_xpath(xpath2).click()
driver.get_cookies()
[{'domain': '.microsoft.com', 'expiry': 1633096351, 'httpOnly': False, 'name': 'MSCC', 'path': '/', 'sameSite': 'None', 'secure': True, 'value': 'cid=gpbpwcf7uk5bjfl5fsg74qhm-c1=2-c2=2-c3=2'}, {'domain': 'account.microsoft.com', 'expiry': 1648734874, 'httpOnly': False, 'name': '_clck', 'path': '/', 'secure': False, 'value': 'hv4nv2'}, {'domain': 'account.microsoft.com', 'httpOnly': False, 'name': 'ShCLSessionID', 'path': '/', 'secure': False, 'value': '1617198120680_0.45882569202435497'}, {'domain': 'account.microsoft.com', 'httpOnly': True, 'name': 'GroupIds', 'path': '/', 'secure': True, 'value': '7ZOAhr9zQ4TIhF_bqq79fMd7dy3Dn60ERSR_qBbLFWgxl-KECaFx7TLtt1ZrTwLV1DcaasCCT8Q6xg-kKHZAPg2'}, {'domain': '.microsoft.com', 'expiry': 1617205310, 'httpOnly': True, 'name': 'bm_sv', 'path': '/', 'secure': False, 'value': '38E8C44FEC85E8E624520830D3CCD5A1~A+Oe2s7fLUAj/l1wBSccnrAL6dk0XI7M3YPdy2AtaaEoXQ1xLfVTnZ6BZI6zIlq7xeCbT4M01v9rTVcw2HgfA0P5ec6IK54lLt061JbAH9TNM6qZu746IWlouhZPyZH/xvjFIEMlI1QOnJVIc5Ur5d1AQrwxlM3wHMc/4AmdXp4='}, {'domain': 'account.microsoft.com', 'expiry': 1617200671, 'httpOnly': False, 'name': 'AMC-MS-CV', 'path': '/', 'secure': True, 'value': 'E9TXnnZHgkSmrOYr.7.33'}, {'domain': 'account.microsoft.com', 'httpOnly': False, 'name': 'ANON', 'path': '/', 'secure': True, 'value': 'A=2E87024C1D09B347ADBF2CDDFFFFFFFF&E=1932&W=1'}, {'domain': 'account.microsoft.com', 'httpOnly': False, 'name': 'canary', 'path': '/', 'secure': True, 'value': 'no'}, {'domain': 'account.microsoft.com', 'httpOnly': False, 'name': 'AMCSecAuth', 'path': '/', 'secure': True, 'value': 'FADCBxS3jx6WnBNTwi8pq3tqm9Jh1cw0EwNmAAAEgAAACKZelWanBJ/egAe2d1NkF5Dgc3xBF4p3ooqcZXuSI2pLbBvi1DYJYHBhzmSkzdvDwNEAIz/k4pduXY4500rk7GmoCmFQI73MMmGFwsIqKislmWB/Yk/yH5nyploxr%2BU5r1Ggwohc4N0xIPnFYIduZopPJwq5OEgVmjXerMdS5qqXlhXrV69vio7p1zhNT/gSqoq5iT6ghWpS7hV2ed8rE%2B2UfEY3pm/E6WOXMziuIOOFvU6YJFc2AjUcCr9NkNFRFMVORHFlLIFDtP3er1mrbA9lm40Ds4lLo0/j/3orutw%2BwndF4HFO45KV6k9cETeJ9JWV1xLwt/3Jxoc55Zn2KQYpH2U4wMPv2a8LCMpB650eLhPbnL0sb/TRrEUVBll1t/x91jvvyMekdhdD7SMNqmXsCYOv6W1ljyZXgbtU8jg9T1hAIgnG3G1s9EPxyTcn0fmWJ3kHYRS1f7quC58EtIlkgLjqZRtrMvpnb/tL4qs0DjyIsbEoNhS2IApns5gpaBwcxvWiI%2B1Whz4QJqDHc%2BZ5QpN05tX9ciD0kFEn5o8h1%2BK9lVhuNi6I/qRoZjwYK0Gby8eCc9OI7wl06WKRXMVnKuE0nPJ/9Q/Q2D31PDHbR9ttM6XyluhgA9ldlrB2Phq9fJ206nQWGoqIZIQZKfm7KYyYhI6eY0iX3SnIPLG7CADZJGT/Wr3ysFilo2ZmQLodv%2BcSQEEAdx3v%2BOFHFjrhQb986o4AvAn3SKzREailO9AjLFZUWFhBEzyxCvyqniYJQoXm/yC9nyeRmC0UXXqL%2BYZkagxgS4ti87cwxnSa03/no820Q%2BTMXOATJaWY2NgdSitvapvj1qiF5/aVLSCd9kvTzAWYFzzocxEbhYU2rC1e7AmCbceu3xkwQn0bjHtxDPI1Hd9q%2BQxTtiYSjs16f4z9YIbPpngBP97GoOWxtHiZ8Z%2BM0A9m28qfYp2w9QmJTkOHgMl3XTrzhbmLsWzdBFW/Boo33Kc7yF%2BDrRv0%2B0%2B6RQ70NxDkS2QOQ9SbgzVVWn5G9jqdfqpaBAJVrLiAnHrWxlsF3NfYlRrXIHWdlLH5J9v3fuSfFj2hXJd2yqrEXRX6o1wshuNRbi2/13w1y0jd3tBf6SSRCQTsU4AUV0lWSCkCoT3p46Sg68oSs15yDQVaCjgzp8KJeRoPrWcPdjUaaFea7URtmuM9mwl1TkDpzNn35sbEfFxA54tTuuXW7TiMVhT9xfJLZ3tFg0pPqD2lWsPOjjNfo0r1cinH8%2BcY93heONiwFaWIyhnP7Wr7l2oYa6h3GT%2Bl16Opke4twydo2AWHmnWhSwU5SJqZyzEPWGJTiZ67huLucP5mNImIwfFghvMvfAC3Qqrii4wLjSYLByZy21GOJ/VNqJxoZrMgGQJy6Ky2Hoji/Lkca27gJBzHPObyNrK8e7%2Bokh%2BQeZRUnn4%2BGleOXNhemoQgRqsqaUEz8Sio9md/ieXnIGli1GcrNK7cDSZyWxdNKWY4N9b60j05Sc3j3Aw0gxBlR82lLDGEZjAv%2BKWt39OqvFyDdD9D8JsPpBetlAtB14g/FLYUVhp/q6hyKmHjbx181rlt5TWqmO7RsNfo64VhW%2BWBsv28xOJ1Wm5bhZMjEcZeQ6JjJ%2BNTvDMmi6mOJCeS0HZ2ZOWl8%2Bz0Zw5cLZ4ct1yxQ8rKqXTWbWieFQOywl5nbfPMvqUDHcfhLhlWbXMlu/xHZ35FDx8aXUAKwqdvN4mrMKEwTw%2BXaQFdczaAm%2BCLaXhgE3ZDd7SGZVy1u7la/nO5UY/ULg1OxC1hAUpfYZB3bEkHpHg2yucLYfIddesYPP61negtafYgUAYC2lqg7eHxrWG4K63Bz1tyfYxzesgk16RzGl6%2BMJjvHJti%2B9/RN1Q7ZuZviLuNGOCkVWKx1lB/2vrKPNSPUVE6wV1GYA7cz03Z3nUrSP8Op0UZRgmi9nyEc41/uApcrg/FvHPj0JwUuH0KWLh%2Bbk05TZ9P7%2Bb4rzmiibB26fOG/FlNVvzOyGdAYwXLq8Vdmx%2BMVNe1OmnbbXVp%2Bvc1pTPmoKoFXzXL6M3ovM128CYiyIdks3yRiLcOeK2a3ZpaiDVUtMfyK24cjOZ%2B84jaunAkoKOuYKvottx%2BE7B16kl/YTFlJo4hQjxvYDWTg%2B7xpXNPbwc5m683f9PqmJoXPxc3lOn1q2NV/tX/1cl1xSR1CtDz1hPpZevbmvz3MAVxpd02VwvIVuzxODKX0bt3K%2BkXfQoXuZRRUh%2BCInSKk34eWRlu40VCv4nYY3s1bqEKxyCqkdhVi%2B8/xKYxI4KSy3bIuhBdootp22bcwcPvVSt%2B6EFnZ1Eu1M3MFvWn3752bWRM3r9yzbdPfdC7exue8fW/G6iZ0Iz1GaW6uQ0fFlaxd3JSmcDXLZtsqh2MG49ggEI0NNoe5UyXxdRoJyb0sPRVqzkFJVSl6afA7bzV/LG1f4tpRJiRsCA%2B8YSfvF0/wCO1aayThgb2KmtLalpmpx/sYQSxloMM%2Bd%2BHvVWMW/V2NKVPbvEhH0yRi5uEZkeKoqCqKQPpo6gk7bc3FUkqXaTejoFPDXfRHsBnZ3KdFfwUABqGYubp4lvwSThUiSxzr3GyjJ42'}, {'domain': 'account.microsoft.com', 'expiry': 1617199920, 'httpOnly': False, 'name': 'Bounced', 'path': '/', 'secure': False, 'value': '2021-03-31T13:42:00.602Z'}, {'domain': 'account.microsoft.com', 'expiry': 1648734114, 'httpOnly': False, 'name': 'MSFPC', 'path': '/', 'sameSite': 'None', 'secure': True, 'value': 'GUID=01d90b81485a42c18c5f1c8e217a52d2&HASH=01d9&LV=202103&V=4&LU=1617198112486'}, {'domain': 'account.microsoft.com', 'httpOnly': False, 'name': 'GRNID', 'path': '/', 'secure': True, 'value': 'cf8e9d7f-fea0-4c90-b437-b0aad409903c'}, {'domain': 'account.microsoft.com', 'httpOnly': False, 'name': 'NAP', 'path': '/', 'secure': True, 'value': 'V=1.9&E=18d8&C=b2RfJ2Ww25IVoU1-EmpW0tETJpPrpBvIIglvxcd-ttzfgAVVnfjG8Q&W=1'}, {'domain': '.microsoft.com', 'expiry': 1617205310, 'httpOnly': True, 'name': 'ak_bmsc', 'path': '/', 'secure': False, 'value': '1364EADDF1EAD179C27360AC00C140795C7A5F5503160000207C646045FF954D~plM6J0sxpwOIIfceeLLrF1pimhlpfOeqNxbS1kdlNi7qDXB31S6GxIlG8TgH8OxMtg86qgYcwXvKVkrJJ+qH08rSVJlQQZV0icvFyvVdJ3EEgwQIBAWgfOJKuiAE9DzUtJWdMUdRhrfWBJz0N7gMGjXZaqe2gVj0/wbEswwa5/cCPwuSFdPfF4pr35SfcKHQSFQAnyA/uN474m85Z7RZVqtkqtvmLB0FoFgzo18CUBsEA='}, {'domain': '.microsoft.com', 'expiry': 1648684798, 'httpOnly': True, 'name': 'MC1', 'path': '/', 'secure': True, 'value': 'GUID=01d90b81485a42c18c5f1c8e217a52d2&HASH=01d9&LV=202103&V=4&LU=1617198112486'}, {'domain': '.microsoft.com', 'expiry': 1617199913, 'httpOnly': False, 'name': 'MS0', 'path': '/', 'sameSite': 'None', 'secure': True, 'value': '3002c516c4a2418f8400b9d5f5b50a99'}, {'domain': '.account.microsoft.com', 'expiry': 1648684798, 'httpOnly': True, 'name': 'MSFPC', 'path': '/', 'secure': True, 'value': 'GUID=01d90b81485a42c18c5f1c8e217a52d2&HASH=01d9&LV=202103&V=4&LU=1617198112486'}, {'domain': '.microsoft.com', 'httpOnly': True, 'name': 'market', 'path': '/', 'secure': True, 'value': 'IT'}]
"""