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
        [buttons.btn_show_cars,buttons.btn_book_a_car],
        [buttons.btn_help,buttons.btn_show_my_bookings]
    ],
    resize_keyboard=True
)
#Клава после нажатия кнопки Забронировать машину
# book_a_car_keyboard = InlineKeyboardMarkup(
#     inline_keyboard=[
#         [buttons.btn_free,buttons.btn_busy],
#     ],
# )


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

#Функция для хода назад
async def registration_back(callback: types.CallbackQuery):
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
        
#Функция для возврата в бронирование
# async def back_booking(callback: types.CallbackQuery):
#     user_id = callback.from_user.id
#     await callback.message.delete()
#     await callback.message.answer(
#         "Выберите, что хотите посмотреть:",
#         reply_markup=book_a_car_keyboard
#     )
#     del booking_step[user_id]

#Общий обработчик кнопки назад
@dp.callback_query(lambda c: c.data == buttons.BACK_CALLBACK)
async def universal_back(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    
    if user_id in registration_step:
        await registration_back(callback)
    
    # elif user_id in booking_step:
    #     await back_booking(callback)
    else:
        await callback.message.delete()

#Обработчик кнопки отмена во время регистрации
@dp.callback_query(lambda c: c.data == buttons.CANCEL_CALLBACK)
async def cancel_registration(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    await callback.message.delete()
    if user_id in registration_step:
        del registration_step[user_id]
        del user_data[user_id]
        await callback.message.answer('Регистрация отменена',reply_markup=unreg_keyboard)
    elif user_id in booking_step:
        del booking_step[user_id]
        del booking_data[user_id]
        await callback.message.answer('Бронирование отменено',reply_markup=reg_keyboard)


#Обработчик кнопки подтвердить во время регистрации
@dp.callback_query(lambda c: c.data == buttons.CONFIRM_CALLBACK)
async def confirm_registration(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    await callback.message.delete()
    if user_id in registration_step:
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
    elif user_id in booking_step:
        user_id = callback.from_user.id
        client_id = database.get_client_by_tgid(user_id)['client_id']
        database.add_booking(
            booking_data[user_id]['car_id'],
            client_id,
            booking_data[user_id]['start_date'],
            booking_data[user_id]['end_date'],
            booking_data[user_id]['total_price'],
            'pending'
        )
        del booking_step[user_id]
        del booking_data[user_id]
        await callback.message.answer(
        'Бронирование подтверждено!\n'
        'Статус: ожидает подтверждения владельцем',
        reply_markup=reg_keyboard
    )


#Функция отображения данных которые заполнял пользователь
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

#Обработчик просмотра всех машин
@dp.message(lambda message: message.text == buttons.btn_show_cars.text)
async def show_cars(message: types.Message):
    cars = database.get_all_cars()
    if not cars:
        await message.answer("Машины отсутствуют")
        return
    all_cars = 'Все машины: \n\n'
    for car in cars:
        all_cars += f'{car[1]} {car[2]} {car[3]} года - {car[4]}₽/день\n\n'
    await message.answer(all_cars)




    
# #Обработчик для кнопки свободных машин
# @dp.callback_query(lambda c: c.data == buttons.FREE_CARS_CALLBACK)
# async def show_free_cars(callback: types.CallbackQuery):
#     await callback.answer()
#     user_id = callback.from_user.id
#     booking_step[user_id] = "free_cars"
#     await callback.message.edit_text("Здесь будет ввод дат и показ свободных машин")

# #Обработчик для кнопки занятых машин
# @dp.callback_query(lambda c: c.data == buttons.BUSY_CARS_CALLBACK)
# async def show_busy_cars(callback: types.CallbackQuery):
#     await callback.answer()
#     user_id = callback.from_user.id
#     booking_step[user_id] = "busy_cars"
#     await callback.message.edit_text("Здесь будет список занятых машин")

#Обработчик кнопки бронирования машин
@dp.message(lambda message: message.text == buttons.btn_book_a_car.text)
async def book_a_car(message: types.Message):
    user_id = message.from_user.id
    booking_step[user_id] = "waiting_start_date"
    booking_data[user_id] = {}
    await message.answer("Введите дату и время желаемой даты аренды в формате - ДД.ММ.ГГГГ ЧЧ:ММ\n" \
    "Пример: 11.11.2011 11:11"
                        ,reply_markup=dur_reg_keyboard)


#Функция показа свободных машин
async def show_available_cars(message:types.Message,user_id: int,cars: list):
    car_btns = []
    if not cars:
        await message.answer('Нет свободных машин')
        return
    for car in cars:
        car_btns.append([InlineKeyboardButton(
                text=f"{car['brand']} {car['model']} {car['year']} года - {car['price_per_day']}₽/день",
                callback_data=f"select_car_{car['car_id']}"
            )
        ])
    car_btns.append([buttons.btn_back, buttons.btn_cancel])
    car_keyboard = InlineKeyboardMarkup(inline_keyboard=car_btns)
    await message.answer('Свободные машины на выбранные даты:\n'
    'Выберите машину:',
    reply_markup=car_keyboard
    )
    booking_step[user_id] = 'waiting_car_choice'

#Обработчик выбора машины
@dp.callback_query(lambda c: c.data.startswith('select_car_'))#если строка начинается с... 
async def select_car(callback:types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    car_id = int(callback.data.split('_')[2])
    booking_data[user_id]['car_id'] = car_id

    price_per_day = database.get_car_price(car_id)

    start = datetime.strptime(booking_data[user_id]['start_date'],'%d.%m.%Y %H:%M')
    end = datetime.strptime(booking_data[user_id]['end_date'], '%d.%m.%Y %H:%M')
    days = (end-start).days
    total_price = price_per_day * days
    booking_data[user_id]['total_price'] = total_price

    await callback.message.edit_text(
        'Вы выбрали машину.'
        f"Даты {booking_data[user_id]['start_date']} - {booking_data[user_id]['end_date']}\n"
        f"Количество дней аренды: {days}\n"
        f"Окончательная стоимость: {total_price}₽\n\n"
        'Подтверждаете бронирование?',
        reply_markup=end_reg_keyboard
    )
    booking_step[user_id] = 'confirm_booking'

#Функция продолжения регистрации(отслеживает шаги регистрации пользователя)
#Ловит все сообщения пользователя независимо от кнопок
async def handle_registration_message(message: types.Message,user_id: int):
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

#Функция для ввода даты начала и конца
async def handle_booking_message(message: types.Message,user_id:int):
    step = booking_step[user_id]
    if step == 'waiting_start_date':
        try:
            start_date = datetime.strptime(message.text,'%d.%m.%Y %H:%M')
            if start_date < datetime.now():
                await message.answer("Дата не может быть в прошлом. Введите снова:")
                return
            booking_data[user_id]['start_date'] = message.text
            booking_step[user_id] = "waiting_end_date"
            await message.answer(
            "Введите дату и время окончания аренды:\n"
            "(ДД.ММ.ГГГГ ЧЧ:ММ)",
            reply_markup=dur_reg_keyboard
        )
        except ValueError:
            await message.answer(
                "Неверный формат. Используйте: ДД.ММ.ГГГГ ЧЧ:ММ\n"
                "Например: 25.12.2025 14:00"
            )
    elif step == 'waiting_end_date':
        try:
            end_date = datetime.strptime(message.text,'%d.%m.%Y %H:%M')
            start_date = datetime.strptime(booking_data[user_id]['start_date'], '%d.%m.%Y %H:%M')
            if end_date <= start_date:
                await message.answer("Дата окончания должна быть позже даты начала. Введите снова:")
                return
            booking_data[user_id]['end_date'] = message.text
            avilable_cars = database.get_avilable_cars(
                booking_data[user_id]['start_date'],
                booking_data[user_id]['end_date']
            )
            if not avilable_cars:
                await message.answer('Нет свободных машин, попробуйте другие даты\n',
                                    reply_markup = reg_keyboard
                )
                return
            await show_available_cars(message,user_id,avilable_cars)
        except ValueError:
            await message.answer(
            "Неверный формат. Используйте: ДД.ММ.ГГГГ ЧЧ:ММ"
        )

@dp.message()
async def handle_all_messages(message: types.Message):
    user_id = message.from_user.id

    if user_id in booking_step:
        await handle_booking_message(message, user_id)

    elif user_id in registration_step:
        await handle_registration_message(message, user_id)
    else:
        await message.answer('Используйте кнопки в меню.')


async def main():
    print("Бот запущен!")
    await dp.start_polling(bot) 

if __name__ == "__main__":
    asyncio.run(main())

