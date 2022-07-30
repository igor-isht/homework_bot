# homework_bot

Бот-ассистент для проверки статуса домашней работы. Каждые 10 минут отправляет запрос на API Яндекс практикума и оповещает об изменении статуса. Также сообщает об ошибках при запросе (когда это возможно). 

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/ln9var/api_final_yatube.git
```

```
cd api_final_yatube
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env (MacOS, Linux)
python -m venv env (Windows)
```

```
source env/bin/activate (MacOS, Linux)
source env/Scripts/activate (Windows)
```

```
python3 -m pip install --upgrade pip
python -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Бот готов к работе!
