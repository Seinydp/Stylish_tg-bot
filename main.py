import aiogram
import asyncio
import logging
import config as config
import art


from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from html import escape



class UserActions(StatesGroup):                                             # Состояния юзера, для ужных хендлеров 
    CHOOSING_SIZE = State() 
    ENTERING_TEXT = State()
    TRY_STYLE = State()

def chose_style(data):                                                      # Присваивание состояние по нажатию кнопки !
    size_to_font = {
        "Маленький": "random-small",
        "Средний": "random-medium",
        "Большой": "random-large"
    }
    return size_to_font.get(data, "random")

def Stylish(stroke, type):                                                  # Стилизация текста
    text = art.text2art(stroke,font=type)
    return(text)

logging.basicConfig(level=logging.INFO)                                     # Логи для просмотра
API_KEY = config.TOKEN                                                      # Получаем токен из отдельного файла
bot = Bot(token=API_KEY)
dp = Dispatcher()
user_router = Router()

change_size = ReplyKeyboardMarkup(                                          # Кнопки выбора размера
    keyboard=[
        [  
            KeyboardButton(text="Маленький"),
            KeyboardButton(text="Средний"),
            KeyboardButton(text="Большой")
        ]
    ],  
    resize_keyboard=True,
    one_time_keyboard=True
)  

change_style = InlineKeyboardMarkup(                                        # Инлайн кнопки взаимодействия с уже готовым текстом
    inline_keyboard=[
           
            [InlineKeyboardButton(text="Поменять style",
                                  callback_data="change")],

            [InlineKeyboardButton(text="Сменить текст", 
                                  callback_data="restart")]
            
    ]
)


dp.include_router(user_router)                                              #хз люблю роутеры

@user_router.message(Command("start"))                                      # Старт простой, 
async def cmd_start(message:Message,state: FSMContext):
    await message.answer("""Привет! Это бот живущий на моем сервере \n
Он Стилизует твой текст символами!  \n
Выбери размер (кликни на кнопку)""",
                         reply_markup=change_size)                          # Добавляем кнопки
    
    await state.set_state(UserActions.CHOOSING_SIZE)                        # Присвоить состояние выборы кнопки (любой текст с кнопки)


@user_router.message(UserActions.CHOOSING_SIZE)                             # Выбор размера| вход только пользователям которым нужно выбрать размер 
async def process_size(message: Message,state:FSMContext):
    if message.text not in ["Маленький","Средний","Большой"]:               #Проверка только на кнопки
        await message.answer("Нажми на кнопку, идиот!")
        return
    await state.update_data(chosen_size = message.text)                     # Занести в дату человека
    await message.answer("""Теперь напишите свой текст(только английский)\n
                         Максимальная длинна 6 символов)""")
    
    await state.set_state(UserActions.ENTERING_TEXT)                        # Состояние выборы текста

@user_router.message(UserActions.ENTERING_TEXT)                             # Вход только для пользователей кто выбрал размер
async def process_text(message:Message, state:FSMContext):
    if len(message.text) < 7:
        user_data = await state.get_data()                                  # Загрузка размера кнопки
        chosen_size = user_data["chosen_size"]                              # Выбор нужного параметра
        

        ansv= Stylish(message.text, chose_style(chosen_size))               # Генерация самого ASCII арта

        safe_text = escape(ansv)                                            # Сейвим символы чтобы не сьезжали

        await state.update_data(chosen_text = message.text)                 # Сейвим текст, для дальнейшей передачи 
        await state.set_state(UserActions.TRY_STYLE)                        # Оставляем последнее состояние, чтобы пользователь ничего лишнего не тыкнул

        await message.answer(
                f"<pre>{safe_text}</pre>",                                  # Добавление ковычек (Отображение в виде кода)
                parse_mode="HTML",
                reply_markup=change_style                                   # Добавление инлайн кнопок
            )
    else:
        await message.answer("Охлади свое траханье! текст короче надо)")

@user_router.callback_query( #
    F.data.in_(["change", "restart"]),                                      # Ловим запросы с инлайн кнопок
    UserActions.TRY_STYLE                                                   # Только в последнем состоянии
)

async def change_style_query(callback: CallbackQuery ,state:FSMContext):    #Обработка
    user_data = await state.get_data()                                      # Получаем всю инфу с которой пользователь дошел до сюда
    user_font = user_data.get("chosen_size")
    user_text = user_data.get("chosen_text")
    

    if callback.data == "change": 
        next_text = Stylish(user_text, chose_style(user_font))              # Генерим текст заново
        safe_text = escape(next_text)                                       # Сейвим символы чтобы не сьезжали

        while (callback.message.html_text) == (f"<pre>{safe_text}</pre>"):  # Пока текст не смениться не меняем 
            next_text = Stylish(user_text, chose_style(user_font))
            safe_text = escape(next_text)

        await callback.message.edit_text(f"<pre>{safe_text}</pre>",
            parse_mode="HTML",
            reply_markup=change_style)
        await callback.answer("стиль обновлен!")                            # Уведомление 

    elif callback.data == "restart": 
        await callback.message.answer("Выберите размер:",
                                      reply_markup=change_size)
        
        await state.set_state(UserActions.CHOOSING_SIZE)                    # Возращаем пользователя на стадию выбора размера
        await callback.answer("♻️ Начинаем заново")

async def main():
    await dp.start_polling(bot)                                             # Запуск бота

if __name__ == "__main__":                                                  # Проверка что запускается ток с этого файла
    try :
        asyncio.run(main()) 
    except Exception as e :
        logging.error(f"Бот упал: {e}")                                     # Лог

