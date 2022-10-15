# SUSTech-Electricity-Bill-Telegram-Bot
SUSTech学生宿舍电余量提醒telegram机器人

## 安装依赖
```shell
pip install -r requirements.txt  # with python3.10 tested
# OR you want to test another version
pip install telegram-bot-python
pip install requests
pip install pause
```

## 启动机器人

启动机器人之前，请先创建一个`config.json`文件，内容参考[config_template.json](config_template.json)

或修改[main.py](./main.py) 文件中的参数 (line 25-35)

程序会尝试读取当前目录下的`config.json`文件，如果没有则使用[main.py](./main.py)中的默认参数

```python
TELEGRAM_BOT_TOKEN = 'PUT_TOKEN_HERE'
DATA_STORE_PATH = '/path/to/subs.pkl'
SUSTECH_USERNAME = 'xxxxxxxx'  # 学号
SUSTECH_PASSWORD = 'passwd'  # 密码
...
SLEEP_TIME = 0.5  # 每次查询的间隔时间
```

```shell
python main.py
# or use systemd, you can use the template service file `./sustech_ebill_bot.service`
```
