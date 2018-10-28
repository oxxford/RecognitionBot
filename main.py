from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
import boto3, requests
import pprint

token = '709661490:AAG6OK_phXyJ1E2_ALwK5HR0eylsTEjBd5A'
REQUEST_KWARGS = {
    'proxy_url': 'socks5://vilunov.me:1488/'
}

s3 = boto3.resource('s3')
ssm = boto3.client('ssm')
rekognition = boto3.client('rekognition')
url = ''

def start(bot, update):
    print('/start')
    bot.send_message(chat_id=update.message.chat_id, text="Hi! I'm Image recognition bot. To start, send me a photo")

def receive_photo(bot, update):
    global url
    file_id = update.message.photo[-1].file_id
    newFile = bot.getFile(file_id)
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="Great, got your photo! Here's a list of things I can do to it:\n"
                         "/detect_emotions")
    filePath = newFile.file_path
    truePath = filePath[filePath.find('photos'):]
    url = 'https://api.telegram.org/file/bot' + token + '/' + truePath

def detect_emotions(bot, update):
    print('detect_emotions')
    global url
    response = requests.get(url)
    response_content = response.content
    rekognition_response = rekognition.detect_faces(Image={'Bytes': response_content}, Attributes=['ALL'])
    res = rekognition_response['FaceDetails'][0]['Emotions']
    message = 'There is\n'
    for em in res:
        conf = int(em['Confidence'])
        type = em['Type']
        em_out = str(conf) + ' percent probability that person in this photo is ' + type +'\n'
        message += em_out
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=message)
    print(message)

updater = Updater(token=token, request_kwargs=REQUEST_KWARGS)
dispatcher = updater.dispatcher

start_handler = CommandHandler('start', start)
receive_photo_handler = MessageHandler(Filters.photo, receive_photo)
detect_emotions_handler = CommandHandler('detect_emotions', detect_emotions)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(receive_photo_handler)
dispatcher.add_handler(detect_emotions_handler)


updater.start_polling()
