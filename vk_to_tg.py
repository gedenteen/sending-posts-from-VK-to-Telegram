# -*- coding: utf-8 -*-

import os
import sys
import vk_api
import requests
import telebot
import configparser 
import ast #для преобразования строки в список
import logging
from telebot.types import InputMediaPhoto
import time # для временных задержок
import os.path # для проверки, существует ли файл
import json

# Считываем настройки
config_path = os.path.join(sys.path[0], 'settings.ini')
config = configparser.ConfigParser()
config.read(config_path)
COUNT = config.get('VK', 'count_of_posts_by_hashtag')
HASHTAG_PREFIX = ast.literal_eval(config.get('VK', 'hashtag_prefix')) #get + преобразовать в list (иначе будет строка)
HASHTAG_POSTFIX = ast.literal_eval(config.get('VK', 'hashtag_postfix')) #get + преобразовать в list (иначе будет строка)
VK_TOKEN = config.get('VK', 'TOKEN', fallback=None)
BOT_TOKEN = config.get('Telegram', 'BOT_TOKEN')
CHANNEL = config.get('Telegram', 'CHANNEL')
INCLUDE_LINK = config.getboolean('Settings', 'INCLUDE_LINK')
PREVIEW_LINK = config.getboolean('Settings', 'PREVIEW_LINK')

# Символы, на которых можно разбить сообщение
message_breakers = [':', ' ', '\n']
max_message_length = 4091

# Инициализируем телеграмм бота
bot = telebot.TeleBot(BOT_TOKEN)

def auth_handler():
    """ При двухфакторной аутентификации вызывается эта функция.
    """

    # Код двухфакторной аутентификации
    key = input("Enter authentication code: ")
    # Если: True - сохранить, False - не сохранять.
    remember_device = True

    return key, remember_device


# Получаем данные из vk.com
def get_data(hashtag, count_vk):
    global LOGIN
    global PASSWORD
    global VK_TOKEN
    global config
    global config_path

    session = requests.Session()

    vk_session= vk_api.VkApi(token=VK_TOKEN)
    vk = vk_session.get_api()
    try:
        response = vk.newsfeed.search(q=hashtag, count=count_vk)
    except vk_api.ApiError as error_msg:
        print("ERROR ", error_msg)
        return

    return response

def read_post(post):
#    global DOMAIN
    global COUNT
    global INCLUDE_LINK
    global bot
    global config
    global config_path

    # Читаем последний извесный id из файла
    id = config.get('Settings', 'LAST_ID')

    ########## отладка
    #print('------------------------------------------------------------------------------------------------')
    #print(post)
    ##################

    # Текст
    text = post['text']

    # Проверяем есть ли что то прикрепленное к посту
    images = []
    links = []
    attachments = []
    if 'attachments' in post:
        attach = post['attachments']
        for add in attach:
            if add['type'] == 'photo':
                img = add['photo']
                images.append(img)
            elif add['type'] == 'audio':
                # Все аудиозаписи заблокированы везде, кроме оффицальных приложений
                continue
            elif add['type'] == 'video':
                video = add['video']
                if 'player' in video:
                    links.append(video['player'])
            else:
                for (key, value) in add.items():
                    if key != 'type' and 'url' in value:
                        attachments.append(value['url'])

#    if INCLUDE_LINK:
#        post_url = "https://vk.com/" + DOMAIN + "?w=wall" + \
#            str(post['owner_id']) + '_' + str(post['id'])
#        links.insert(0, post_url)
    text = '\n'.join([text] + links)
    send_posts_text(text)

    if len(images) > 0:
        image_urls = list(map(lambda img: max(
            img["sizes"], key=lambda size: size["type"])["url"], images))
        #print(image_urls)
        try:
            bot.send_media_group(CHANNEL, map(lambda url: InputMediaPhoto(url), image_urls))
        except:
            print('some problem with images')

    # Проверяем есть ли репост другой записи
    if 'copy_history' in post:
        copy_history = post['copy_history']
        copy_history = copy_history[0]
        #print('--copy_history--')
        #print(copy_history)
        text = copy_history['text']
        send_posts_text(text)

        # Проверяем есть ли у репоста прикрепленное сообщение
        if 'attachments' in copy_history:
            copy_add = copy_history['attachments']
            copy_add = copy_add[0]

            # Если это ссылка
            if copy_add['type'] == 'link':
                link = copy_add['link']
                text = link['title']
                send_posts_text(text)
                img = link['photo']
                send_posts_img(img)
                url = link['url']
                send_posts_text(url)

            # Если это картинки
            if copy_add['type'] == 'photo':
                attach = copy_history['attachments']
                for img in attach:
                    image = img['photo']
                    send_posts_img(image)

    # Записываем id в файл
    config.set('Settings', 'LAST_ID', str(post['id']))
    with open(config_path, "w") as config_file:
        config.write(config_file)

def create_tags():
    global COUNT
    global INCLUDE_LINK
    global HASHTAG_PREFIX
    global HASHTAG_POSTFIX
    global bot
    global config
    global config_path

    hashtag_prefix  = HASHTAG_PREFIX
    hashtag_postfix = HASHTAG_POSTFIX
    hashtags = []
    for prefix in hashtag_prefix:
        for postfix in hashtag_postfix:
            hashtags.append(prefix + postfix)
    print('count of tags = ', len(hashtags), '\n')
    
    global VK_TOKEN
    vk_session= vk_api.VkApi(token=VK_TOKEN)
    vk = vk_session.get_api()

    # создать папку "posts_id", если она еще не создана (в ней будут храниться "базы данных")
    if not os.path.exists("posts_id"): os.mkdir("posts_id") 

    for hashtag in hashtags:  
        print('hashtag = ', hashtag)

        response = vk.newsfeed.search(q=hashtag, count=COUNT)
        response = reversed(response['items'])

        idsFromFile = [] 
        fileName = 'posts_id\/' + hashtag + '.txt';

        # проверка, есть ли файл (он содержат ID записей для данного хэштега):
        if os.path.isfile(fileName):
            fileDescr = open(fileName, 'r')
            for id_ in fileDescr:
                #print(id_)
                idsFromFile.append(int(id_))
            print("idsFromFile:", idsFromFile)
        else:
            print('It looks like there is no necessary file. But nothing, I will create a file')
        
        # Откроет для добавления нового содержимого. 
        # Создаст новый файл для записи, если не найдет с указанным именем.
        fileDescr = open(fileName, 'a+') 


        i = 1; # счетчик, сколько всего постов обработано (с начала запуска скрипта)
        # цикл по всем полученным постам:
        for post in response:
            print('i = ', i, ", post ID =", str(post['id']))
            i += 1

            # если этот пост уже был прочитан (отправлен в канал в телеграме), то пропускаем:
            if int(post['id']) in idsFromFile:
                print('i have already read this post')
            else: # иначе читаем, отправляем и записываем в этот самый файл
                print('new post!')
                read_post(post)
                fileDescr.write(str(post['id']) + '\n')

            time.sleep(30) # задержка, потому что ВК не разрешает обращаться слишком часто
        # закончили с постами по этому хэштегу

        fileDescr.close();
        print('\n')
    # закончили с этим хэштегом


### Отправляем посты в телеграмм
# Текст
def send_posts_text(text):
    global CHANNEL
    global PREVIEW_LINK
    global bot

    if text == '':
        print('no text')
    else:
        # В телеграмме есть ограничения на длину одного сообщения в 4091 символ, разбиваем длинные сообщения на части
        for msg in split(text):
            bot.send_message(CHANNEL, msg, disable_web_page_preview=not PREVIEW_LINK)


def split(text):
    global message_breakers
    global max_message_length

    if len(text) >= max_message_length:
        last_index = max(
            map(lambda separator: text.rfind(separator, 0, max_message_length), message_breakers))
        good_part = text[:last_index]
        bad_part = text[last_index + 1:]
        return [good_part] + split(bad_part)
    else:
        return [text]


# Изображения
def send_posts_img(img):
    global bot
    
    # Находим картинку с максимальным качеством
    url = max(img["sizes"], key=lambda size: size["type"])["url"]
    bot.send_photo(CHANNEL, url)


if __name__ == '__main__':
    create_tags()
