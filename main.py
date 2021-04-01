from selenium.webdriver import Chrome

import msrewards

driver = Chrome()

rewards = msrewards.MicrosoftRewards(driver)

rewards.go_to_home()
rewards.restore_cookies()
rewards.go_to_home()

rewards.execute_activities()

print()
