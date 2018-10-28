from telegram.ext import Updater
from telegram.ext import CommandHandler

token = ''
REQUEST_KWARGS = {
    
}


def start(bot, update):
    print('/start')
    bot.send_message(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!")


updater = Updater(token=token, request_kwargs=REQUEST_KWARGS)
dispatcher = updater.dispatcher
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

updater.start_polling()
