# coding=utf8

######################################################
#
# Tia Text Assistant - Internet tasks without using Data/Wi-Fi
# written by Jonathan Schwartz (jonathanschwartz30@gmail.com)
#
######################################################

from __future__ import print_function
import re
import wikipedia
import requests
from textblob import TextBlob

import general_message_helpers as msg_gen
import api_keys as SHEETS

# INFORMATION FUNCTIONS #######


def wikipedia_request(command_body):
    return wiki_split(wikipedia.summary(command_body))


def wiki_split(text_input):
    text_input = re.sub('"', "\'", str(text_input))
    text_input = re.sub("'", "\'", str(text_input))
    text_input = re.sub('%', " percent", str(text_input))
    wiki = TextBlob(text_input)
    chunked = wiki.sentences

    total_string = []
    for i in range(0, len(chunked)):

        total_string.append(str(chunked[i]))

    total_string = " 📖 \n\n 📖 ".join(total_string)
    return total_string


def wolfram_request(input):
    print("triggered wolf alert inside with: " + str(input))
    original_input = input
    input = re.sub(" ", "%20", str(input))
    url = "http://api.wolframalpha.com/v2/query?appid=" + \
        SHEETS.WOLFRAM_API + "&input=" + input + "&output=json"
    print(url)
    json_data = requests.get(url).json()
    result = "Question: '" + str(original_input).capitalize() + "'\n\n📚 Answer: " + str(
        json_data['queryresult']['pods'][1]['subpods'][0]['plaintext'])
    return result
    

def trigger_wolfram(resp, sender_info):
    print("Wolfram Triggered")
    # print(resp)
    msg_gen.store_reply_in_mongo(
                                       wolfram_request(
                                           resp['_text']),
                                       sender_info,
                                       "🔭 Q & A 🔭")


def trigger_wiki(resp, sender_info):
    print("Wikipedia Triggered")
    # print(resp)
    # print(sender_info)
    wikiSearch = resp['_text']
    try:
        wikiSearch = resp['entities']['wikipedia_search_query'][0]['value']
    except BaseException:
        wikiSearch = msg_gen.extract_quoted_text(resp['_text'])
    
    print("Wit.AI Wikisearch term: " + wikiSearch)
    msg_gen.store_reply_in_mongo(
                                       wikipedia_request(
                                           wikiSearch),
                                       sender_info,
                                       "🔎 Wikipedia 🔎")

    # print(resp)
