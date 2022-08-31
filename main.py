import json
import logging
import os
import pickle
import time
from copy import deepcopy
from typing import Optional
from threading import Lock

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

import requests

import pause
import datetime

from sustech_cas_login import connect

TELEGRAM_BOT_TOKEN = 'PUT_TOKEN_HERE'

DATA_STORE_PATH = '/path/to/subs.pkl'
QUERY_URL = 'http://ehall.sustech.edu.cn/dxggyw/sys/sdjfgl/paymentController/getFjyl.do?ldid={}&mph={}'
SUSTECH_USERNAME = 'xxxxxxxx'  # 学号
SUSTECH_PASSWORD = 'passwd'  # 密码

ERR = -1e-3
SLEEP_TIME = 0.5  # in seconds


def get_remains(session: requests.Session, building: str, room_id: str) -> float:
    url = QUERY_URL.format(building, room_id)
    reply = session.get(url)
    try:
        dfyl = json.loads(reply.text)['data']['data'][0]['dfyl']
        return dfyl
    except (json.JSONDecodeError, KeyError, IndexError):
        return ERR


class Subscriptions:
    def __init__(self, updater: Updater):
        # self.data: {str('chat_id'): tuple(str('building'), str('room_id'), int('threshold')),}
        self.data: dict
        self.updater = updater
        self.lock = Lock()
        if os.path.exists(DATA_STORE_PATH):
            self.load_data()
        else:
            self.data = {}
            self.store_data()

    def load_data(self):
        try:
            with open(DATA_STORE_PATH, 'rb') as f:
                self.data = pickle.load(f)
        except pickle.PickleError:
            self.data = {}

    def store_data(self):
        try:
            with open(DATA_STORE_PATH, 'wb') as f:
                pickle.dump(self.data, f)
        except pickle.PickleError:
            pass

    def add_job(self, chat_id: int, building: str, room_id: str, threshold: int) -> bool:
        with self.lock:
            ret = chat_id in self.data
            self.data[chat_id] = (building, room_id, threshold)
            self.store_data()
        return ret

    def get_job(self, chat_id: int) -> Optional[tuple[str, str,  int]]:
        with self.lock:
            if chat_id not in self.data:
                return None
            else:
                return self.data[chat_id]

    def del_job(self, chat_id: int) -> bool:
        with self.lock:
            ret = chat_id in self.data
            if ret:
                del self.data[chat_id]
                self.store_data()
        return ret

    def send_all(self):
        data: dict
        with self.lock:
            data = deepcopy(self.data)
        sess = connect(SUSTECH_USERNAME, SUSTECH_PASSWORD)
        for chat_id, (building, room_id, threshold) in data.items():
            remains = get_remains(sess, building, room_id)
            if remains == ERR:
                self.updater.bot.send_message(chat_id=chat_id, text='获取余量失败')
            elif remains <= threshold:
                self.updater.bot.send_message(chat_id=chat_id, text=f'余量不足: `{remains:.2f} <= {threshold}`')
            time.sleep(SLEEP_TIME)

SUBS: Subscriptions

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext) -> None:
    """Sends brief explanation on how to use the bot."""
    update.message.reply_markdown_v2('Hi\. Use `/subscribe <二期书院栋数> <房间号> <电费阈值>` to subscribe, more help by `/help`')


def bot_help(update: Update, context: CallbackContext) -> None:
    """Send full Help to user"""
    update.message.reply_markdown_v2("""
    help:
    • Use `/subscribe <二期书院栋数> <房间号> <电费阈值rmb>` to subscribe
    • Use `/cancel` to cancel your subscription
    • Use `/get` to get your subscription details

    example:
    • `/subscribe 11 312 50` 以获取通知当学生宿舍11栋312寝室的电量低于50元, 每日一次
    • 当已subscribe时再次subscribe会取消之前的订阅，相当于先运行一次 `/cancel`
    """)


def add_job(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    try:
        building = context.args[0]
        if building not in ('11', '12', '13', '14', '15', '16'):
            update.message.reply_text('栋数错误')
            return
        room_id = context.args[1]
        threshold = int(context.args[2])
        if threshold <= 0:
            update.message.reply_text('threshold 应为大于0整数')
            return
        SUBS.add_job(chat_id, building, room_id, threshold)
        update.message.reply_text('ok')
    except (IndexError, ValueError):
        update.message.reply_markdown_v2('Usage: `/subscribe <二期书院栋数> <房间号> <电费阈值>`')


def get_subs(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    job = SUBS.get_job(chat_id)
    if job is None:
        update.message.reply_text('You have no active subscription.')
    else:
        update.message.reply_markdown_v2(f'You are subscribed to `building={job[0]}`, `room={job[1]}` with threshold `{job[2]}CNY`')


def cancel(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if SUBS.del_job(chat_id):
        update.message.reply_text('cancel: ok')
    else:
        update.message.reply_text('no active subscription')


def main() -> None:
    """Run bot."""
    # Create the Updater and pass it your bot's token.
    # put your bot's token here
    updater = Updater(TELEGRAM_BOT_TOKEN)
    global SUBS
    SUBS = Subscriptions(updater)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', bot_help))
    dispatcher.add_handler(CommandHandler('subscribe', add_job))
    dispatcher.add_handler(CommandHandler('cancel', cancel))
    dispatcher.add_handler(CommandHandler('get', get_subs))

    # Start the Bot
    updater.start_polling()

    next_day_8am = datetime.datetime.combine(datetime.date.today() + datetime.timedelta(days=1), datetime.time(8, 0))

    while True:
        pause.until(next_day_8am)
        next_day_8am = next_day_8am + datetime.timedelta(days=1)
        SUBS.send_all()


if __name__ == '__main__':
    main()
