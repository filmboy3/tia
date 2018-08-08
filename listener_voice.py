#!/usr/bin/env python
import pika
import time
import mongo_helpers as mongo
import google_voice_hub as gv
import google_sheets_api_storage as SHEETS

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

browser = gv.start_google_voice(SHEETS.GV_EMAIL, SHEETS.GV_PASSWORD)

channel.queue_declare(queue='google_voice_queue', durable=True)
print('[*] Waiting for messages from GOOGLE-VOICE QUEUE ... To exit press CTRL+C')

def callback(ch, method, properties, body):   
    body = mongo.convert_message_from_bytes(body)
    current_reply = body['current_chunk']
    print("[x] Received Message from GOOGLE-VOICE QUEUE: '" + str(body['result'][current_reply]) + "' to be sent to '" + str(body['from']) + "'")
    ch.basic_ack(delivery_tag = method.delivery_tag)
    # print(body)
    gv.process_reply(body, browser)
    print(" [x] Done")

channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback,
                      queue='google_voice_queue')

channel.start_consuming()