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


edit_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="ФИО", callback_data="edit_name")],
    [InlineKeyboardButton(text="Телефон", callback_data="edit_phone")],
    [InlineKeyboardButton(text="Серия паспорта", callback_data="edit_series")],
    [InlineKeyboardButton(text="Номер паспорта", callback_data="edit_number")],
    [InlineKeyboardButton(text="Кем выдан", callback_data="edit_issued")],
    [InlineKeyboardButton(text="Дата выдачи", callback_data="edit_date")],
    [InlineKeyboardButton(text="Прописка", callback_data="edit_registration")],
    [buttons.btn_back, buttons.btn_cancel]
])

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
        [buttons.btn_confirm,buttons.btn_edit],
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

@dp.callback_query(lambda c: c.data == buttons.CONFIRM_CALLBACK)
async def confirm_registration(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
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
    
    


@dp.callback_query(lambda c: c.data == buttons.CANCEL_CALLBACK)
async def cancel_registration(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    del registration_step[user_id]
    del user_data[user_id]
    await callback.message.answer('Регистрация отменена')
    
@dp.callback_query(lambda c: c.data == buttons.BACK_CALLBACK)
async def back_registration(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id

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

@dp.callback_query(lambda c: c.data == buttons.EDIT_CALLBACK)
async def egit_registration(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    await callback.message.edit_text(
        "Выберите, что хотите изменить:",
        reply_markup=edit_keyboard
    )

@dp.callback_query(lambda c: c.data == "edit_name")
async def edit_name(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    registration_step[user_id] = "edit_name"
    await callback.message.edit_text("Введите ФИО:")

@dp.callback_query(lambda c: c.data == "edit_phone")
async def edit_phone(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    registration_step[user_id] = "edit_phone"
    await callback.message.edit_text("Введите телефон:")

@dp.callback_query(lambda c: c.data == "edit_series")
async def edit_series(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    registration_step[user_id] = "edit_series"
    await callback.message.edit_text("Введите серию паспорта:")

@dp.callback_query(lambda c: c.data == "edit_number")
async def edit_number(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    registration_step[user_id] = "edit_number"
    await callback.message.edit_text("Введите номер паспорта:")

@dp.callback_query(lambda c: c.data == "edit_issued")
async def edit_issued(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    registration_step[user_id] = "edit_issued"
    await callback.message.edit_text("Кем выдан паспорт:")

@dp.callback_query(lambda c: c.data == "edit_date")
async def edit_date(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    registration_step[user_id] = "edit_date"
    await callback.message.edit_text("Введите дату выдачи паспорта:")

@dp.callback_query(lambda c: c.data == "edit_registration")
async def edit_reg(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    registration_step[user_id] = "edit_reg"
    await callback.message.edit_text("Введите прописку:")


@dp.message()
async def continue_reg(message: types.Message):
    user_id = message.from_user.id
    if user_id not in registration_step:
        await message.answer('Используйте кнопки в меню.')
        return
    step = registration_step[user_id]

    if isinstance(step,str):
        
    
    else:
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
        elif step == 8:

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
                await message.answer('Регистрация успешно завершена! \n'
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













