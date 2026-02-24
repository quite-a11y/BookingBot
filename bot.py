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

start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [buttons.btn_start]
    ],
    resize_keyboard=True
)

reg_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [buttons.btn_show_cars,buttons.btn_show_my_bookings],
        [buttons.btn_help]
    ],
    resize_keyboard=True
)

dur_reg_keyboard = InlineKeyboardMarkup(
    keyboard=[
        [buttons.btn_back,buttons.btn_cancel],
    ],
    resize_keyboard=True
)

end_reg_keyboard = InlineKeyboardMarkup(
    keyboard=[
        [buttons.btn_confrim,buttons.btn_edit],
    ],
    resize_keyboard=True
)

unreg_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [buttons.btn_show_cars],
        [buttons.btn_help,buttons.btn_reg]
    ],
    resize_keyboard=True
)


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





@dp.message()
async def continue_reg(message: types.Message):
    user_id = message.from_user.id
    if user_id not in registration_step:
        await message.answer('Используйте кнопки в меню.')
    else:
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
                await message.answer('Неверный формат даты. Введите в формате ДД.ММ.ГГГГ',
                reply_markup=dur_reg_keyboard)
        elif step == 7:
            user_data[user_id]['registration'] = message.text
            user_data[user_id]['telegram_id'] = user_id
            await message.answer(f'''Ваши данные:\n
                                ФИО: {user_data[user_id]["full_name"]}\n
                                Телефон: {user_data[user_id]["phone"]}\n
                                Серия паспорта: {user_data[user_id]["passport_series"]}\n
                                Номер паспорта: {user_data[user_id]["passport_number"]}\n
                                Кем выдан: {user_data[user_id]["passport_issued"]}\n
                                Дата выдачи: {user_data[user_id]["date_of_issue"]}\n  
                                Место регистрации: {user_data[user_id]["registration"]}\n
                                ''',reply_markup=end_reg_keyboard)                             
            try:
                client_id = database.add_client(
                    user_data[user_id]['full_name'],
                    user_data[user_id]['phone'],
                    user_data[user_id]['passport_series'],
                    user_data[user_id]['passport_number'],
                    user_data[user_id]['passport_issued'],
                    user_data[user_id]['date_of_issue'],
                    user_data[user_id]['registration'],
                    user_data[user_id]['telegram_id']
                )
                del registration_step[user_id]
                del user_data[user_id]
                await message.answer('Регистрация успешно завершена! \n' \
                'Теперь вы можете бронировать машины',
                reply_markup=reg_keyboard
                )
            except Exception as e:
                await message.answer(f'Ошибка при регистрации {e}. \n'
                                     'Попробуйте сначала ', reply_markup=dur_reg_keyboard)
                del registration_step[user_id]
                del user_data[user_id]
async def main():
    print("Бот запущен!")
    await dp.start_polling(bot) 

if __name__ == "__main__":
    asyncio.run(main())













