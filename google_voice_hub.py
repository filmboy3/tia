# -*- coding: UTF-8 -*-
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
import math
import mongo_helpers as mongo
import api_keys as SHEETS


def start_google_voice(emailAddress, emailPassword):
    chromedriver = SHEETS.CHROME_PATH

    options = webdriver.ChromeOptions()
    # options.add_argument('headless')
    options.add_argument("--incognito")
    options.add_argument('window-size=1200x600')  # optional

    browser = webdriver.Chrome(
        executable_path=chromedriver,
        chrome_options=options)
    # print("Browser: " + str(browser))
    browser.get('https://voice.google.com/')
    browser.find_element_by_xpath("""//*[@id="header"]/div[2]/a""").click()
    email = browser.find_element_by_xpath("""//*[@id="identifierId"]""")
    email.click()
    email.send_keys(emailAddress)
    email.send_keys(Keys.RETURN)
    time.sleep(3)

    password = browser.find_element_by_xpath(
        """//*[@id="password"]/div[1]/div/div[1]/input""")
    password.send_keys(emailPassword)
    password.send_keys(Keys.RETURN)
    time.sleep(8)
    browser.get('https://voice.google.com/u/0/messages')
    return browser


def initiate_gv_send(number, browser, message):
    print("Initiated actual GV sending message to: " + str(number))
    interface_prep = setup_message(number, browser)
    enter_message(interface_prep, message, browser)
    time.sleep(2)
    delete_previous_conversation(browser)
    browser.get('https://voice.google.com/u/0/messages')


def trigger_send_reply(record, browser):
    current_chunk = record['current_chunk']
    current_message = record['result'][current_chunk]
    print("Staged Message: " + str(current_message))
    # try:
    #     number = record['from']
    #     initiate_gv_send(number, browser, current_message)
    #     mongo.change_db_user_value(record, "current_sms_id", record['sms_id'])
    #     updated_record = {
    #         "current_sms_id": record['sms_id'],
    #         "current_chunk": (current_chunk + 1)
    #     }
    #     mongo.update_record(record, updated_record, mongo.message_records)
    #     mongo.change_db_message_value(record, "current_sms_id", record['sms_id'])
    # except:
    #     print("Error inside Trigger_send_reply")
    #     # This is a trouble spot
    # try:
    number = record['from']
    initiate_gv_send(number, browser, current_message)
    mongo.change_db_user_value(record, "current_sms_id", record['sms_id'])
    updated_record = {
        "current_sms_id": record['sms_id'],
        "current_chunk": (current_chunk + 1)
    }
    mongo.update_record(record, updated_record, mongo.message_records)
    mongo.change_db_message_value(record, "current_sms_id", record['sms_id'])
    # except:
    #     print("Error inside Trigger_send_reply")
    #     # This is a trouble spot
    
    updated_message = mongo.message_records.find_one({"sms_id": record['sms_id']})
    return updated_message

def check_launch_time(record, browser):
    print("Placeholder for launch_time_checker")

def send_all_messages(record, browser):
    print("Sending all Messages at Once...")
    record = mongo.message_records.find_one({"sms_id": record['sms_id']})
    time.sleep(1)
    while (record['current_chunk'] < record['chunk_len']):
        record = trigger_send_reply(record, browser)


def send_next_message(record, browser):
    record = mongo.message_records.find_one({"sms_id": record['sms_id']})
    time.sleep(1)
    if (record['current_chunk'] < record['chunk_len']):
        print("Sending Next Message") 
        trigger_send_reply(record, browser)


def process_reply(record, browser):
    record = mongo.message_records.find_one({"sms_id": record['sms_id']})
    time.sleep(1)
    if record['launch_time'] == "NOW":
        if record['send_all_chunks'] == "SINGLE_CHUNKS":
            send_next_message(record, browser)
        else:
            send_all_messages(record, browser)
    else:
        check_launch_time(record, browser)
        

def make_sms_chunks(text, send_all_chunks, sms_size=300):
    count = len(text)
    # print(count)

    chunk_note = "\nFor more 📲, text MORE\nFor all 📲, text ALL"
    
    if send_all_chunks == "ALL_CHUNKS":
        chunk_note = ""

    number_of_chunks = int(math.ceil(count / float(350)))
    chunk_array = []
    if number_of_chunks == 1:
        # print("No chunking Necessary")
        chunk_array.append(text)
        chunk_result = (1, chunk_array)
    else:
        # print("Chunking Necessary")
        sms_end = sms_size
        sms_start = 0
        while (sms_end < count):
            while (text[sms_end] != "\n"):
                sms_end = sms_end + 1
            # print("sms_end after: " + str(sms_end) + "\n")
            current_chunk = text[sms_start:sms_end]
            # print(chunk_array)
            chunk_array.append(current_chunk)
            sms_start = sms_end
            sms_end = sms_end + sms_size
        final_chunk = text[sms_start:]
        chunk_array.append(final_chunk)
        for i in range(0, len(chunk_array) - 1):
            chunk_array[i] = chunk_array[i] + \
                "\n\n⬇️ (" + str(i + 1) + " of " + str(len(chunk_array)) + ") ⬇️" + chunk_note

        # print("\n\nChunk Array formmated: \n\n" + str(chunk_array) + "\n\n")
        chunk_result = (len(chunk_array), chunk_array)
    return chunk_result

def sizing_sms_chunks(text, send_all_chunks):
    print("Optimizing SMS chunking")
    try:
        chunk_set = make_sms_chunks(text, send_all_chunks)
    except BaseException:
        try:
            chunk_set = make_sms_chunks(text, send_all_chunks, 250)
            print("Triggered lower SMS chunking size @ 250")
        except BaseException:
            try:
                chunk_set = make_sms_chunks(text, send_all_chunks, 200)
                print("Triggered lower SMS chunking size @ 200")
            except BaseException:
                try:
                    chunk_set = make_sms_chunks(text, send_all_chunks, 150)
                    print("Triggered lower SMS chunking size @ 150")
                except BaseException:
                    try:
                        chunk_set = make_sms_chunks(text, send_all_chunks, 100)
                        print("Triggered lower SMS chunking size @ 100")
                    except BaseException:
                        chunk_set = make_sms_chunks(text, send_all_chunks, 50)
                        print("Triggered lower SMS chunking size @ 50")
    return chunk_set


def enter_message(message, gv_message, browser):
    JS_ADD_TEXT_TO_INPUT = """
    var elm = arguments[0], txt = arguments[1];
    elm.value += txt;
    elm.dispatchEvent(new Event('change'));
    """
    browser.execute_script(JS_ADD_TEXT_TO_INPUT, message, gv_message)
    time.sleep(1)
    message.send_keys(Keys.CONTROL, 'a')
    message.send_keys(Keys.CONTROL, 'c')
    message.send_keys(Keys.CONTROL, 'v')
    time.sleep(1)
    message.send_keys(Keys.RETURN)
    time.sleep(1)


def delete_previous_conversation(browser):
    conversation_box = browser.find_element_by_xpath("""//*[@id="messaging-view"]/div/div/md-content/div/gv-conversation-list/md-virtual-repeat-container/div/div[2]/div[1]/div/gv-text-thread-item/gv-thread-item/div/div[2]/div/gv-annotation
""")
    conversation_box.click()
    time.sleep(1)
    settings_dots = browser.find_element_by_xpath(
        """//*[@id="messaging-view"]/div/div/md-content/gv-thread-details/div/div[1]/gv-message-list-header/div/div[2]/div/md-menu/button/md-icon""")
    settings_dots.click()
    time.sleep(1)
    browser.find_element_by_xpath("""//button[@aria-label='Delete']""").click()
    time.sleep(1)
    try:
        browser.find_element_by_xpath(
            """//md-checkbox[@aria-label='I understand']""").click()
    except BaseException:
        pass
    time.sleep(1)
    browser.find_element_by_xpath(
        """//button[@gv-test-id='delete-thread-confirm']""").click()


def setup_message(gv_number, browser):
    initiate_Message = browser.find_element_by_xpath(
        """//*[@id="messaging-view"]/div/div/md-content/div/div/div""")
    initiate_Message.click()
    time.sleep(1)

    # toForm = browser.find_element_by_xpath(
    #     """//*[@id="messaging-view"]/div/div/md-content/gv-thread-details/div/div[1]/gv-recipient-picker/div/md-content/md-chips/md-chips-wrap/div/div/input""")
    toForm = browser.find_element_by_xpath(
        """//*[@id="_md-chips-wrapper-3"]/div/div/input""")
    # toForm = browser.find_element_by_xpath(
    #      """//*[@id="messaging-view"]/div/div/md-content/gv-thread-details/gv-make-call/div/div/div/div/div/md-input-container""")
    toForm.click()
    toForm.send_keys(gv_number)
    toForm.send_keys(Keys.ARROW_DOWN)
    time.sleep(1)
    toForm.send_keys(Keys.RETURN)
    time.sleep(1)
    time.sleep(1)
    message = browser.find_element_by_xpath(
        """//textarea[@aria-label='Type a message']""")
    message.click()
    return message
