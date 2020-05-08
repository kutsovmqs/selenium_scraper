from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import psycopg2
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


def save_clause(clause_id, category_id):
    item = driver.find_element_by_xpath(xpath % clause_id).text
    sql_string = 'INSERT INTO clauses(clause_category_id, text, original_id) ' \
                 'VALUES(%s, %s, %s) RETURNING id'
    db_cursor.execute(sql_string, (category_id, item, clause_id))
    db_clause_id = db_cursor.fetchall()[0]
    conn.commit()
    save_samples(db_clause_id)


def save_samples(db_clause_id):
    sample_xpath = '//div[@data-clause-id=%s]//div[@class="split-buttons__item"]//a'
    samples = driver.find_elements_by_xpath(sample_xpath % clause_id)
    for sample in samples:
        sample_link = sample.get_attribute('href')
        sql_string = 'INSERT INTO clauses_links(clause_id, link) VALUES(%s, %s)'
        db_cursor.execute(sql_string, (db_clause_id, sample_link,))
        conn.commit()


def get_clause_category_id(clause_name):
    sql_string = 'SELECT COALESCE((SELECT id FROM clause_categories WHERE name=%s), 0)'
    db_cursor.execute(sql_string, (clause_name,))
    category_id = db_cursor.fetchall()[0]

    if category_id[0] == 0:
        sql_string = 'INSERT INTO clause_categories(name) VALUES(%s) RETURNING id'
        db_cursor.execute(sql_string, (clause_name,))
        category_id = db_cursor.fetchall()[0]
        conn.commit()
    return category_id[0]


PAGE_CLAUSE_COUNT = 10
PAGE_RELOAD_COUNT = 3
DELAY = 5
db_login = os.environ.get("DB_LOGIN")
db_password = os.environ.get("DB_PASSWORD")

clauses = get_clauses_list()
base_url = "http://www.lawinsider.com/clause/%s"
xpath = '//div[@data-clause-id=%d]/div[@class="snippet-content"]'
virtual_display = bool(os.environ.get("RUN_FROM_DOCKER"))
testing = bool(os.environ.get("TESTING"))
if testing:
    dbname = "LI_scraper_test"
else:
    dbname = "LI_scraper"


if virtual_display:
    display = Display(visible=0, size=(1280, 2560))
    display.start()

next_cursor = ''

with open('iofiles/logs.csv', 'a') as logfile:
    LogWriter = csv.writer(logfile)
    with psycopg2.connect(dbname=dbname, user=db_login, password=db_password, host='localhost') as conn:
        with conn.cursor() as db_cursor:
            for clause in clauses:
                category_id = get_clause_category_id(clause)

                print_log_item("--------"+clause+"--------")
                print_log_item("start time: "+time.asctime()+"     database: " + dbname)
                driver = webdriver.Chrome(options=get_chrome_options())
                link = base_url % clause + next_cursor
                driver.get(link)
                authorize(driver)
                print_log_item(link)
                scraped = 0
                next_cursor = "start"

                while next_cursor != "":
                    first_clause_id = int(driver.find_elements_by_xpath('//div[@data-clause-id]')[0]
                                          .get_attribute('data-clause-id'))
                    for i in range(PAGE_RELOAD_COUNT):
                        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                        time.sleep(DELAY)

                    last_clause_id = int(driver.find_elements_by_xpath('//div[@data-clause-id]')[-1]
                                         .get_attribute('data-clause-id'))
                    for clause_id in range(first_clause_id, last_clause_id+1):
                        save_clause(clause_id, category_id)
                        scraped = scraped + 1

                    next_cursor = driver.find_elements_by_xpath('//div[@data-next-cursor]')[-1]\
                        .get_attribute('data-next-cursor')
                    if next_cursor != "":
                        print_log_item("scraped clauses: " + str(scraped) + "   time: " + time.asctime())
                        link = base_url % clause + '?cursor=' + next_cursor
                        print_log_item(link)
                        driver.get(link)
                        try:
                            wait = WebDriverWait(driver, 30)
                            element = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@data-next-cursor]')))
                        except TimeoutException:
                            print_log_item("ALERT: TIMEOUT EXCEPTION (PAGE RELOADING)" + "   time: " + time.asctime())
                            driver.close()
                            time.sleep(1260)
                            driver = webdriver.Chrome(options=get_chrome_options())
                            driver.get(link)
                            authorize(driver)
                            print_log_item(link)
                # driver.close()
                print_log_item("end time: "+time.asctime())
if virtual_display:
    display.stop()

