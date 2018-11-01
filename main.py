from telegram.ext import Updater
from telegram.ext import CommandHandler

token = '709661490:AAG6OK_phXyJ1E2_ALwK5HR0eylsTEjBd5A'
REQUEST_KWARGS = {
    'proxy_url': 'socks5://vilunov.me:1488/'
}


def start(bot, update):
    print('/start')
    bot.send_message(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!")


updater = Updater(token=token)
dispatcher = updater.dispatcher
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

updater.start_polling()
