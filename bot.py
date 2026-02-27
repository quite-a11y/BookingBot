import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup,KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import database
import buttons

TOKEN = "8445110973:AAGMyJFrIHrSHcHgwn1bWvCeOKmDlqud_mY"
bot = Bot(token=TOKEN)
dp = Dispatcher()

user_data = {}
booking_data = {}
registration_step = {} #Отслеживание шагов регистрации
booking_step = {} #Отслеживание шагов бронирования

#Кнопка старт
start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [buttons.btn_start]
    ],
    resize_keyboard=True
)
#Клава до регистрации
unreg_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [buttons.btn_show_cars],
        [buttons.btn_help,buttons.btn_reg]
    ],
    resize_keyboard=True
)
#Клава в течении регистрации
dur_reg_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [buttons.btn_back,buttons.btn_cancel],
    ],
)
#Клава в конце регистрации
end_reg_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [buttons.btn_confirm],
        [buttons.btn_back,buttons.btn_cancel]
    ],
)
#Клава после регистрации
reg_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [buttons.btn_show_cars,buttons.btn_show_my_bookings],
        [buttons.btn_help]
    ],
    resize_keyboard=True
)

#Обработчик /start
@dp.message(Command('start'))
async def cmd_start_command(message: types.Message):
    await message.answer(
        "Нажми кнопку START, чтобы начать работу:",
        reply_markup=start_keyboard
    )

#Обработчик кнопки старт
@dp.message(lambda message: message.text == buttons.btn_start.text)
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    client = database.get_client_by_tgid(user_id)
    if client:
        await message.answer(
            f'С возвращением, {client["full_name"]}!',
            reply_markup=reg_keyboard
        )
    else:
        await message.answer(
            f'Привет, {message.from_user.first_name}!\n'
            'Для регистрации нажми кнопку ниже. \n', 
            reply_markup=unreg_keyboard
        )

#Обработчик кнопки регистрации
@dp.message(lambda message: message.text == buttons.btn_reg.text)
async def start_reg(message:types.Message):
    user_id = message.from_user.id
    client = database.get_client_by_tgid(user_id)
    if client:
        await message.answer('Вы уже зарегестрированы!')
        return
    registration_step[user_id] = 1
    user_data[user_id] = {}
    await message.answer(
        "Регистрация: \n" 
        "Шаг 1 из 7 \n" 
        "Введите ваше ФИО:",
        reply_markup=dur_reg_keyboard
    )

#Обработчик кнопки назад во время регистрации
@dp.callback_query(lambda c: c.data == buttons.BACK_CALLBACK)
async def back_registration(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    await callback.message.delete()

    if registration_step[user_id] > 1:
        registration_step[user_id] -= 1
        questions = {
            1: "Введите ваше ФИО:",
            2: "Введите ваш номер телефона:",
            3: "Введите серию паспорта:",
            4: "Введите номер паспорта:",
            5: "Кем выдан паспорт?",
            6: "Дата выдачи (ДД.ММ.ГГГГ):",
            7: "Введите вашу прописку:"
        }

        await callback.message.answer(f'Шаг {registration_step[user_id]} из 7\n'
                                      f'{questions[registration_step[user_id]]}',
                                      reply_markup=dur_reg_keyboard)
        
#Обработчик кнопки отмена во время регистрации
@dp.callback_query(lambda c: c.data == buttons.CANCEL_CALLBACK)
async def cancel_registration(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    await callback.message.delete()
    del registration_step[user_id]
    del user_data[user_id]
    await callback.message.answer('Регистрация отменена',reply_markup=unreg_keyboard)

#Обработчик кнопки подтвердить во время регистрации
@dp.callback_query(lambda c: c.data == buttons.CONFIRM_CALLBACK)
async def confirm_registration(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    await callback.message.delete()
    user_name = user_data[user_id]['full_name']
    database.add_client(
        user_data[user_id]['full_name'],
        user_data[user_id]['phone'],
        user_data[user_id]['passport_series'],
        user_data[user_id]['passport_number'],
        user_data[user_id]['passport_issued'],
        user_data[user_id]['date_of_issue'],
        user_data[user_id]['registration'],
        user_id
    )
    del registration_step[user_id]
    del user_data[user_id]
    await callback.message.answer(f'Поздравляю, {user_name}, вы успешно зарегестрировались! \n'
                                  'Теперь вам доступны машины для бронирования',
    reply_markup=reg_keyboard)

async def show_user_data(message: types.Message, user_id: int):
    try:
        await message.delete()
    except:
        pass

    await message.answer(
        f'''Ваши данные:
        ФИО: {user_data[user_id]['full_name']}
        Телефон: {user_data[user_id]['phone']}
        Серия паспорта: {user_data[user_id]['passport_series']}
        Номер паспорта: {user_data[user_id]['passport_number']}
        Кем выдан: {user_data[user_id]['passport_issued']}
        Дата выдачи: {user_data[user_id]['date_of_issue']}
        Место регистрации: {user_data[user_id]['registration']}
        ''',
        reply_markup=end_reg_keyboard
    )
    registration_step[user_id] = 8

@dp.message()
async def continue_reg(message: types.Message):
    user_id = message.from_user.id
    if user_id not in registration_step:
        await message.answer('Используйте кнопки в меню.')
        return
    step = registration_step[user_id]
    if step == 1:
        user_data[user_id]['full_name'] = message.text
        registration_step[user_id] = 2
        await message.answer('Шаг 2 из 7 \n' 
        'Введите ваш номер телефона:',
        reply_markup=dur_reg_keyboard)
    elif step == 2:
        user_data[user_id]['phone'] = message.text
        registration_step[user_id] = 3
        await message.answer('Шаг 3 из 7:\n'
        'Введите серию паспорта:',
        reply_markup=dur_reg_keyboard)
    elif step == 3:
        user_data[user_id]['passport_series'] = message.text
        registration_step[user_id] = 4
        await message.answer("Шаг 4 из 7: \n"
        "Введите номер паспорта:",
        reply_markup=dur_reg_keyboard)
    elif step == 4:
        user_data[user_id]['passport_number'] = message.text
        registration_step[user_id] = 5
        await message.answer("Шаг 5 из 7: \n"
        "Кем выдан паспорт?",
        reply_markup=dur_reg_keyboard)
    elif step == 5:
        user_data[user_id]['passport_issued'] = message.text
        registration_step[user_id] = 6
        await message.answer("Шаг 6 из 7: \n" 
        "Дата выдачи (ДД.ММ.ГГГГ):",
        reply_markup=dur_reg_keyboard)
    elif step == 6:
        try:
            datetime.strptime(message.text,'%d.%m.%Y')
            user_data[user_id]['date_of_issue'] = message.text
            registration_step[user_id] = 7
            await message.answer("Шаг 7 из 7: \n"
            "Введите вашу прописку:",
            reply_markup=dur_reg_keyboard)
        except:
            await message.answer('Неверный формат даты.\n' 
            'Повторно введите в формате (ДД.ММ.ГГГГ):',
            reply_markup=dur_reg_keyboard)

    elif step == 7:
        user_data[user_id]['registration'] = message.text
        user_data[user_id]['telegram_id'] = user_id
        await show_user_data(message, user_id)
async def main():
    print("Бот запущен!")
    await dp.start_polling(bot) 

if __name__ == "__main__":
    asyncio.run(main())

