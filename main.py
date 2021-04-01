from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options

import msrewards

edge_win_ua = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    " AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763"
)
chrome_android_ua = (
    "Mozilla/5.0 (Linux; Android 9; SM-G960F Build/PPR1.180610.011; wv) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157"
    " Mobile Safari/537.36"
)

uas = [edge_win_ua, chrome_android_ua]

# standard points from activity
driver = Chrome()

rewards = msrewards.MicrosoftRewards(driver)
rewards.go_to_home()
rewards.execute_todo_activities()

driver.quit()

# points from searches
for ua in uas:
    options = Options()
    options.add_argument(f"user-agent={ua}")
    driver = Chrome(options=options)

    msrewards.MicrosoftRewards(driver).execute_searches()

    driver.quit()
