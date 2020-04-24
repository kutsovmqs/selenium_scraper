from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import csv
from pyvirtualdisplay import Display
import os


def authorize(driver):
    print("authorization...")
    if len(driver.find_elements_by_xpath('//button[@event-action="sign in"]')) > 0:
        driver.find_element_by_xpath('//button[@event-action="sign in"]').click()
        driver.find_element_by_name('email').send_keys(os.environ.get("LAWINSIDER_LOGIN"))
        driver.find_element_by_name('password').send_keys(os.environ.get("LAWINSIDER_PASSWORD"))
        driver.find_element_by_name('password').send_keys(Keys.ENTER)
        time.sleep(DELAY)
        print("-- authorized")


def get_chrome_options():
    print("get chrome options...")
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    return chrome_options


def print_log_item(log_str):
    print(log_str)
    LogWriter.writerow([log_str])


def get_clauses_list():
    with open('iofiles/input.csv', 'r') as file:
        reader = csv.reader(file)
        clauses_list = []
        for row in reader:
            clauses_list.append(" ".join(row))
    return clauses_list


PAGE_CLAUSE_COUNT = 10
PAGE_RELOAD_COUNT = 3
DELAY = 5

# clauses = ['expulsion', 'incentive-bonus', 'counterparts']  # properties
clauses = get_clauses_list()  # properties
base_url = "http://www.lawinsider.com/clause/%s"
xpath = '//div[@data-clause-id=%d]/div[@class="snippet-content"]'
virtual_display = bool(os.environ.get("RUN_FROM_DOCKER"))

if virtual_display:
    display = Display(visible=0, size=(1280, 2560))
    display.start()

with open('iofiles/logs.csv', 'a') as logfile:
    LogWriter = csv.writer(logfile)

    for clause in clauses:
        print_log_item("--------"+clause+"--------")
        print_log_item("start time: "+time.asctime())

        driver = webdriver.Chrome(options=get_chrome_options())
        link = base_url % clause
        driver.get(link)
        authorize(driver)

        clause_id = 1
        next_cursor = ''
        items = []

        print_log_item(link)

        with open('iofiles/%s.csv' % clause, 'w') as outfile:
            LIWriter = csv.writer(outfile)
            while len(driver.find_elements_by_xpath(xpath % clause_id)) > 0:
                items.append(driver.find_element_by_xpath(xpath % clause_id).text)
                if clause_id % PAGE_CLAUSE_COUNT == 0:
                    for item in items:
                        LIWriter.writerow([item])
                    items = []
                    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                    time.sleep(DELAY)

                if clause_id % (PAGE_CLAUSE_COUNT * PAGE_RELOAD_COUNT) == 0:
                    next_cursor = driver.find_elements_by_xpath('//div[@data-next-cursor]')[PAGE_RELOAD_COUNT-1].get_attribute('data-next-cursor')

                if next_cursor != "" and clause_id % (PAGE_CLAUSE_COUNT * PAGE_RELOAD_COUNT) == 0:
                    print_log_item("scraped clauses: " + str(clause_id) + "   time: "+time.asctime())
                    link = base_url % clause + '?cursor=' + next_cursor
                    driver.get(link)
                    print_log_item(link)

                    time.sleep(DELAY)
                clause_id = clause_id + 1
            for item in items:
                LIWriter.writerow([item])
            print_log_item("scraped clauses: " + str(clause_id - 1) + "   time: "+time.asctime())
        driver.close()
        print_log_item("end time: "+time.asctime())
    if virtual_display:
        display.stop()
