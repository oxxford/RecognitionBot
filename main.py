from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
import boto3, requests

token = '709661490:AAG6OK_phXyJ1E2_ALwK5HR0eylsTEjBd5A'
REQUEST_KWARGS = {
    'proxy_url': 'socks5://vilunov.me:1488/'
}

s3 = boto3.resource('s3')
ssm = boto3.client('ssm')
rekognition = boto3.client('rekognition')


def start(bot, update):
    print('/start')
    bot.send_message(chat_id=update.message.chat_id, text="Hi! I'm Image recognition bot. To start, send me a photo")
    # file = update.message.photo
    # while len(file) == 0:
    #     updates = bot.getUpdates
    #     for u in updates:
    #         if u.message.photo:
    #             file = updates.message.photo
    # bot.send_message(chat_id=update.message.chat_id,
    #                  text="got photo")
    # print()

def photo(bot, update):
    file_id = update.message.photo[-1].file_id
    newFile = bot.getFile(file_id)
    #newFile.download('test.jpg')
    bot.sendMessage(chat_id=update.message.chat_id, text="download succesfull")
    #url = 'https://api.telegram.org/bot'+token+'/getFile?file_id=' + file_id
    #response1 = requests.get(url)
    #response1_content = response1.content
    #filePath = response1_content['result']['file_path']
    url = 'https://api.telegram.org/file/bot' + token + '/' + 'photos/file_0.jpg'
    response = requests.get(url)
    response_content = response.content
    rekognition_response = rekognition.detect_faces(Image={'Bytes': response_content}, Attributes=['ALL'])
    print(rekognition_response)

updater = Updater(token=token, request_kwargs=REQUEST_KWARGS)
dispatcher = updater.dispatcher
start_handler = CommandHandler('start', start)
# sendPhoto_handler = CommandHandler('sendPhoto', sendPhoto)

dispatcher.add_handler(start_handler)
#dispatcher.add_handler(sendPhoto_handler)

photo_handler = MessageHandler(Filters.photo, photo)
dispatcher.add_handler(photo_handler)


updater.start_polling()
