import config
from pymongo import MongoClient
import telebot
import random
import math
import asyncio
from telebot import types



from functools import reduce
def factors(n):
    return set(reduce(list.__add__,
                ([i, n//i] for i in range(1, int(n**0.5) + 1) if n % i == 0)))

mongoPassword = '';
APP_CONFIG  = {
    "mongo":
        {"hostString":"9a.mongo.evennode.com:27017,9b.mongo.evennode.com:27017/088e12ee0f336c47cbb32ddbce9cfea4?replicaSet=eu-9",
         "user":"088e12ee0f336c47cbb32ddbce9cfea4",
         "db":"088e12ee0f336c47cbb32ddbce9cfea4"}
}


client = MongoClient("mongodb://" + APP_CONFIG['mongo']['user'] + ":" + mongoPassword + "@" +
    APP_CONFIG['mongo']['hostString'])

bot = telebot.TeleBot(config.token)

db = client['088e12ee0f336c47cbb32ddbce9cfea4']
users = db.users
games = {}



def is_num(a):
    try:
        b = float(a)
        return True
    except:
        return False
def gameExist(id):
    try:
        d = games[id]
        return True
    except:
        return False


stdKeyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
stdKeyboard.add(types.KeyboardButton(config.startGameButtonText),types.KeyboardButton(config.ratingButtonText))

def makeAnsKeyboard(ans):
    print("MAKE IT")
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    options = [ans]
    for i in range(3):
        num = random.randint(1,7)
        if random.random() < 0.5:
            num*=-1

        options.append(ans+num)
    random.shuffle(options)
    for i in range(4):
        options[i] = types.KeyboardButton(options[i])
    for i in range(0,4,2):
        keyboard.add(*options[i:i+2])
    return keyboard
signs = ['+','-','*','/']
def makeTask():
    taskStr = ''
    firstPart = math.floor(random.uniform(-50,+50))
    taskStr+=str(firstPart) + " "
    sign = math.floor(random.uniform(0, 4))
    taskStr+=signs[sign] + " "
    ans = 0
    secondPart = 0
    if (sign == 0):
        secondPart = math.floor(random.uniform(-50,+50))
        ans = firstPart+secondPart
    elif (sign == 1):
        secondPart = math.floor(random.uniform(0,+50))
        ans = firstPart-secondPart
    elif (sign == 2):
        secondPart = math.floor(random.uniform(-50,+50))
        ans = firstPart * secondPart
    else:
        firstPartFactors = list(factors(abs(firstPart)))
        if len(firstPartFactors) == 2:
            secondPart = 2
        else:
            firstPartFactors.sort()
            secondPart = firstPartFactors[math.floor(random.uniform(1,len(firstPartFactors)-0.1))]
        ans = firstPart/secondPart
        if math.floor(ans) == math.ceil(ans):
            ans = int(ans)
    taskStr += str(secondPart)
    return {"ans": ans,"task": taskStr}
@bot.message_handler(commands=['start'])
def  greeting(message):
    # bot.send_message(message.chat.id, "Привет", parse_mode='html', reply_markup=makeAnsKeyboard(1))
    bot.send_message(message.chat.id, "Привет",parse_mode='html',reply_markup=stdKeyboard)
@bot.message_handler(content_types=['text'])
def check(message):
    if message.text == config.startGameButtonText:
        startGame(message.chat.id,0,message.chat.id)
    elif message.text == config.ratingButtonText:
        myRating(message.chat.id)
    elif is_num(message.text):
        gameAns(message.chat.id,message.text)

def startGame(id,counter,chatid):
    if gameExist(id) and counter==0:
        bot.send_message(id,config.gameStartedText,parse_mode='html')
    else:
        task = makeTask()
        games[id] = {}
        games[id]['chatid'] = chatid
        games[id]["ans"] = task["ans"]
        games[id]["counter"] = counter
        print("ANS:", task["ans"])
        bot.send_message(id, task["task"], parse_mode='html',reply_markup=makeAnsKeyboard(task['ans']))
        games[id]['msgid'] = bot.send_message(id, "Времени осталось: 5").message_id

        asyncio.run(timer(id))


async def timer(id,):
    print('hello')
    was = games[id]['counter']
    for i in range(config.timeGiven+1):
        print(5-i)
        try:
            if was != games[id]['counter']:
                break
        except:
            break
        try:
            bot.edit_message_text(message_id = games[id]['msgid'], chat_id = games[id]['chatid'], text = "Времени осталось: " + str(config.timeGiven - i))
        except:
            pass
        await asyncio.sleep(1)
    try:
        if was == games[id]['counter']:
            bot.edit_message_text(message_id = games[id]['msgid'], chat_id = games[id]['chatid'], text = "Время вышло.")
            endGame(id)
            deleteGame(id)
    except:
        pass
def gameAns(id,givenAns):
    if gameExist(id):
        ans = games[id]["ans"]
        if ans == float(givenAns):
            print("Right Answer")
            bot.delete_message(chat_id=games[id]["chatid"],message_id=games[id]["msgid"])
            bot.send_message(id, "Верно.", parse_mode='html')
            if games[id]["counter"] < config.gamesAmount:
                startGame(id,games[id]["counter"]+1,games[id]["chatid"])
            else:
                endGame(id)
                deleteGame(id)
        else:
            bot.send_message(id, "Не верно. Правильный ответ: " + str(ans), parse_mode='html')
            endGame(id)
            deleteGame(id)
    else:
        print(games)
        bot.send_message(id, "Игра не начата", parse_mode='html')

def endGame(id):
    answered = games[id]["counter"]
    text = 'Игра закончена. \n'
    if answered == config.gamesAmount:
        text+='Вы решили все примеры (' + str(config.gamesAmount) + ")"
    else:
        text+='Количество решённых примеров: ' + str(answered)
    updateRating(id,games[id]["counter"])
    bot.send_message(id,text,reply_markup=stdKeyboard)
def myRating(id):
    data = users.find_one({"id":id})
    if data is not None:
        text = "Всего решено: " + str(data['allSolved']) +"\nЛучшая попытка: " + str(data['maxSolved'])
        bot.send_message(id,text)
    else:
        bot.send_message(id,"Вы не решили ни одного примера")
def updateRating(id,solved):
    data = users.find_one({"id":id})
    if data is not None:
        data['allSolved']+=solved
        data['maxSolved'] = max(data['maxSolved'],solved)
        data['id'] = id
        users.find_one_and_replace({"id":id},data)
    else:
        if solved:
            data = {}
            data['id'] = id
            data['allSolved'] = solved
            data['maxSolved'] = solved
            users.insert_one(data)

def deleteGame(id):
    games.pop(id)

bot.polling(none_stop=True)


