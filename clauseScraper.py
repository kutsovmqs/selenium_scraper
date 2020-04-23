from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import csv
from pyvirtualdisplay import Display


LOGIN = "roman@parleypro.com"
PASSWORD = "VBCyj9sypr!i5kj"

PAGE_CLAUSE_COUNT = 10
PAGE_RELOAD_COUNT = 10
DELAY = 5

# clauses = ['expulsion', 'incentive-bonus', 'counterparts']  # properties
clauses = ['expulsion', 'incentive-bonus']  # properties
base_url = "http://www.lawinsider.com/clause/%s"
xpath = '//div[@data-clause-id=%d]/div[@class="snippet-content"]'


def authorize(driver):
    print("authorization...")
    if len(driver.find_elements_by_xpath('//button[@event-action="sign in"]')) > 0:
        driver.find_element_by_xpath('//button[@event-action="sign in"]').click()
        driver.find_element_by_name('email').send_keys(LOGIN)
        driver.find_element_by_name('password').send_keys(PASSWORD)
        driver.find_element_by_name('password').send_keys(Keys.ENTER)
        time.sleep(DELAY)
        print("-- authorized")


def get_chrome_options():
    print("get chrome options...")
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    return chrome_options


# display = Display(visible=0, size=(1280, 2560))
# display.start()
with open('output/logs.csv', 'w') as logfile:
    LogWriter = csv.writer(logfile)

    for clause in clauses:
        driver = webdriver.Chrome(options=get_chrome_options())
        driver.get(base_url % clause)
        authorize(driver)
        clause_id = 1
        items = []
        with open('output/%s.csv' % clause, 'w') as outfile:
            LIWriter = csv.writer(outfile)
            next_cursor = driver.find_element_by_xpath('//div[@data-next-cursor]').get_attribute(
                'data-next-cursor')
            LogWriter.writerow([next_cursor])

            # while next_cursor != '' and len(driver.find_elements_by_xpath(xpath % clause_id)) > 0:
            while len(driver.find_elements_by_xpath(xpath % clause_id)) > 0:
                items.append(driver.find_element_by_xpath(xpath % clause_id).text)
                if clause_id % PAGE_CLAUSE_COUNT == 0:
                    for item in items:
                        LIWriter.writerow([item])
                    items = []
                    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                    time.sleep(DELAY)
                    next_cursor = driver.find_element_by_xpath('//div[@data-next-cursor]').get_attribute('data-next-cursor')

                if next_cursor != "" and clause_id % (PAGE_CLAUSE_COUNT * PAGE_RELOAD_COUNT) == 0:
                    driver.get(base_url % clause + '?cursor=' + next_cursor)
                    time.sleep(DELAY)
                clause_id = clause_id + 1
            for item in items:
                LIWriter.writerow([item])
                next_cursor = ""

        driver.close()
    # display.stop()
