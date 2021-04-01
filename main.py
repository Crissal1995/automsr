from selenium.webdriver import Chrome

import msrewards

driver = Chrome()

rewards = msrewards.MicrosoftRewards(driver)

# rewards.go_to("https://www.google.com")
# rewards.restore_cookies()
rewards.go_to_home()

rewards.execute_activities(rewards.get_todo_activities())
