# Описание
Этот скрипт основан на скрипте из этого урока: https://nikovit.ru/blog/pishem-bota-peresylki-soobshcheniy-iz-vk-v-telegram-na-python/
Различия:
1. Авторизация через VK-токен, а не через логин+пароль
2. Поиск по хэштегам, а не определенной групе
3. Пересланные посты сохраняются в "базу данных", чтобы не пересылать их снова

# Установка
1. Создать бота в Телеграме. Для этого нужно написать @BotFather (это официальный бот телеграма) команду `/newbot` и придумать имя. В итоге мы должны получить токен бота, который понадобится потом.
1. Создать канал в Телеграме, в администраторы этого канала добавить нашего бота.
1. Установить Python (версии 3.*), во время установки поставить галочку на "Add Python to path"
1. Установить библиотеки через pip: 
```
pip install vk_api
pip install pyTelegramBotAPI
```
5. Получить VK-токен здесь: https://vkhost.github.io/ . Для этого нужен аккаунт в ВК. Примечание: необходимо получать новый токен, если скрипт запускается на другом компьютере.
6. В файл `setting.ini` подставить токен созданного бота, имя созданной группы (перед именем вставить '@') и VK-токен.
7. В этом же файле нужно указать hashtag_prefix и hashtag_prefix - это 2 части хэштегов. Они конкотенируются и по получившися тегам будут искаться записи. В принципе, можно написать тег полностью в hashtag_prefix или hashtag_postfix.
8. Запустить run.bat

# Ссылки
Телеграмм-группа, куда пересылаются посты для моего скрипта: https://t.me/channelforexplorestrategygames

# Алгоритм работы
1. Из файла `setting.ini` экспортируются информация для скрита `vk_to_tg.py`
2. По указанным хэштегам ищутся записи в vk.com через VK API.
3. Найденные записи (точнее, их id) сравниваются с теми записями, которые уже были пересланы. Для сравнения используется "база данных" - это просто тестовые файлы в папке `posts_id`. Для каждого хэштега создается одноименный файл, в котором перечислены все id пересланных постов.
4. Если запись новая, то она отправляется в телеграм-канал, указанный в настройках.
