import os
import requests
import numpy as np
import sqlite3 as sl
import matplotlib.pyplot as plt

from datetime import datetime
from matplotlib.dates import date2num, AutoDateLocator


db = 'tg_user.db'


def create_db():
    if db not in os.listdir():
        with sl.connect(db) as con:
            request = """
            CREATE TABLE users (
                tgid integer,
                first_name text,
                last_name text,
                username text
            );
            """
            con.execute(request)


def is_user_exist(username):
    with sl.connect(db) as con:
        request = """
        SELECT username
        FROM users
        WHERE username = '{0}';
        """.format(username)
        result = con.execute(request)
        if len(list(result)) != 0:
            return True
        else:
            return False


def add_new_user(tg_id, first_name, second_name, username):
    with sl.connect(db) as con:
        request = """
        INSERT INTO users (tgid, first_name, last_name, username)
        VALUES(?, ?, ?, ?);
        """
        con.executemany(request, [(tg_id, first_name, second_name, username)])


def del_user(username):
    with sl.connect(db) as con:
        request = """
        DELETE FROM users
        WHERE username = '{0}';
        """.format(username)
        con.execute(request)


def is_data_transfer_off():
    data = requests.get('http://84.237.52.214/current/data/60/Kluchi/0/0/').json()
    if data['depth'] is None:
        return True
    else:
        return False


def get_all_user_id():
    with sl.connect(db) as con:
        request = """
        SELECT tgid 
        FROM users;
        """
        result = list(con.execute(request))
        all_user_id = []
        for i in result:
            all_user_id.append(i[0])
        return all_user_id


def get_extend(x, y):
    x_comp = (max(x) - min(x)) * 0.1 * (1/len(x))
    y_comp = (max(y) - min(y)) * 0.1 * (1 / len(y))
    return [min(x) - x_comp, max(x) + x_comp, min(y) - y_comp, max(y) + y_comp]


def str_to_datetime(array):
    new_array = []
    for i in array:
        new_array.append(datetime.strptime(i, '%d.%m.20%y %H-%M-%S'))
    return new_array


# make picture for message
def get_temp_report():
    data = requests.get('http://84.237.52.214/current/data/1440/Kluchi/0/0/').json()
    temp = np.array(data['temp'])
    depth = np.array(data['depth'])
    times = date2num(str_to_datetime(data['times']))

    pic_folder = 'static/'

    fig, ax = plt.subplots()
    ax.set_title(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    graph = ax.imshow(temp[::-1], cmap='jet',
                      interpolation='none', aspect='auto',
                      extent=get_extend(times, depth))
    ax.xaxis_date()
    ax.xaxis.set_major_locator(AutoDateLocator(minticks=3, maxticks=5))
    ax.set_xlabel('Время [с]')
    ax.set_ylabel('Глубина [м]')
    fig.colorbar(graph, ax=ax)
    ax.invert_yaxis()
    fig.savefig(pic_folder + 'current.png')

    return float(str(temp.mean())[:5]), float(str(np.max(temp) - np.min(temp))[:5])
