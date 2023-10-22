import time
import schedule
import telebot as tl

from multiprocessing import Process
from telebot import types
from func import add_new_user, is_user_exist, del_user, create_db
from func import get_all_user_id, is_data_transfer_off, get_temp_report


bot = tl.TeleBot('*')


class ProcSchedule:
    def __init__(self):
        self.is_sensor_working = True

    @staticmethod
    def start_schedule():
        schedule.every(60).minutes.do(ProcSchedule.check_data_transfer)
        schedule.every().day.at('12:00').do(ProcSchedule.make_report)

        while True:
            schedule.run_pending()
            time.sleep(1)

    @staticmethod
    def make_report():
        if not is_data_transfer_off():
            temps = get_temp_report()
            text = '''
            📕 Ежедневный отчет:\n\nСредняя температура на DTS за день: {0} 🌡\nМаксимальный перепад температур: {1} 🤒
            '''.format(temps[0], temps[1])
            all_id = get_all_user_id()
            for i in all_id:
                bot.send_message(i, text)

    def check_data_transfer(self):
        if is_data_transfer_off() and self.is_sensor_working:
            all_id = get_all_user_id()
            for i in all_id:
                bot.send_message(i, '🆘 Отсутствуют данные за последние часы!')
            self.is_sensor_working = False


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('DTS Monitor')
    btn2 = types.KeyboardButton('Отчеты')
    markup.add(btn1, btn2)
    bot.send_message(message.from_user.id, '👋 Здравствуйте! Что вас интересует?', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def get_text_messages(message):

    if message.text == 'DTS Monitor':
        bot.send_message(
            message.from_user.id,
            '🖥 Приложение монитринга доступно по ' + '[ссылке](http://84.237.52.214/visualisation/)',
            parse_mode='Markdown')

    if message.text == 'Отчеты':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('📒 Я хочу получать отчеты')
        btn2 = types.KeyboardButton('❌ Я больше не хочу получать отчеты')
        btn3 = types.KeyboardButton('📋 Получить текущий отчет')
        markup.add(btn1, btn2, btn3)
        bot.send_message(message.from_user.id,
                         '❓ Какие операции с отчетами вас интересуют?',
                         reply_markup=markup)

    # add user
    if message.text == '📒 Я хочу получать отчеты':
        if is_user_exist(message.from_user.username):
            bot.send_message(message.from_user.id,
                             '⚠️ Пользователь {0} уже получает отчеты!'.format(message.from_user.username))
        else:
            add_new_user(message.from_user.id, message.from_user.first_name,
                         message.from_user.last_name, message.from_user.username)
            bot.send_message(message.from_user.id,
                             '✅ Пользователь {0} добавлен в базу данных!'.format(message.from_user.username))

    # delete user
    if message.text == '❌ Я больше не хочу получать отчеты':
        if is_user_exist(message.from_user.username):
            del_user(message.from_user.username)
            bot.send_message(message.from_user.id,
                             '✅ Пользователь {0} удален из базы данных!'.format(message.from_user.username))
        else:
            bot.send_message(message.from_user.id,
                             '⚠️ Пользователя {0} нет в базе данных!'.format(message.from_user.username))

    # get current report
    if message.text == '📋 Получить текущий отчет':
        temps = get_temp_report()
        text = '''
        📒 Текущий отчет:\n\nСредняя температура на DTS за день: {0} 🌡\nМаксимальный перепад температур: {1} 🤒
        '''.format(temps[0], temps[1])
        img = open('static/current.png', 'rb')
        bot.send_photo(message.from_user.id, img)
        bot.send_message(message.from_user.id, text)


def start_process():
    Process(target=ProcSchedule.start_schedule, args=()).start()


if __name__ == '__main__':
    create_db()
    start_process()
    bot.polling(none_stop=True, interval=0)
