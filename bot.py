import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup,KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
import database
import buttons

with open('api.txt','r',encoding='utf-8') as r:
    line = r.read()
    print(line)

#systemctl restart valera_bot
TOKEN = line
bot = Bot(token=TOKEN)
dp = Dispatcher()
# ADMIN_ID = 1027977984
ADMIN_ID = 1027977985

user_data = {}
booking_data = {}
registration_step = {} #Отслеживание шагов регистрации
booking_step = {} #Отслеживание шагов бронирования
admin_car_data = {}
admin_car_step = {}
admin_last_car_message = {}
admin_delete_car_id = {}
temp_client_photos = {}  # {user_id: {'step': 1, 'passport': None, 'license': None}}

#Клава загрузки фото документов сейчас/позже
documents_choice_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [buttons.btn_upload_now, buttons.btn_upload_later]
    ]
)

#Клава выбора срока аренды
indefinite_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Ввести количество дней", callback_data="enter_days")],
        [InlineKeyboardButton(text="Договоримся при встрече (больше 30 дней)", callback_data="indefinite_rent")]
    ]
)

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

#Только клава с кнопкной отмены
dur_reg_keyboard2 = InlineKeyboardMarkup(
    inline_keyboard=[
        [buttons.btn_cancel],
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
        "Нажми кнопку внизу, чтобы начать работу:",
        reply_markup=start_keyboard
    )

#Админ |

#Клава админа
admin_main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [buttons.btn_admin_cars],
        [buttons.btn_admin_all_bookings]
    ],
    resize_keyboard=True
)

admin_cars_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [buttons.btn_add_car,buttons.btn_admin_all_cars],
        [buttons.btn_delete_car,buttons.btn_back_to_admin]
    ],
    resize_keyboard=True
)
#Обработчик кнопки назад 
@dp.message(lambda message: message.text == "Назад")
async def back_to_main_menu(message: types.Message):
    await message.answer(
        "Главное меню:",
        reply_markup=reg_keyboard
    )
#Обработчик кнопки все машины у админа
@dp.message(lambda message: message.text == buttons.btn_admin_all_cars.text)
async def admin_show_all_cars(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    cars = database.get_all_cars()
    if not cars:
        await message.answer('В базе нет машин')
        return
    cars_buttons = []
    for car in cars:
        cars_buttons.append([KeyboardButton(text=f"{car['brand']} {car['model']}")])
    # cars_buttons.append([buttons.btn_back_to_admin])
    cars_keyboard = ReplyKeyboardMarkup(
        keyboard=cars_buttons,
        resize_keyboard=True
    )
    await message.answer(
        "Список всех машин:",
        reply_markup=cars_keyboard
    )

#Обработчик кнопки старт
@dp.message(lambda message: message.text == buttons.btn_start.text)
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    client = database.get_client_by_tgid(user_id)
    if client:
        if user_id == ADMIN_ID:
            await message.answer(
                f'С возвращением, Админ {client["full_name"]}!',
                reply_markup=admin_main_keyboard 
            )
        else:
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

#Обработчик кнопки управление машинами
@dp.message(lambda message: message.text == buttons.btn_admin_cars.text)
async def admin_cars_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(
        "Управление машинами",
        reply_markup=admin_cars_keyboard
    )
#Обработчик кнопки назад
@dp.message(lambda message: message.text == buttons.btn_back_to_admin.text)
async def back_to_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(
        "Возврат к админ-панеле",
        reply_markup=admin_main_keyboard
    )

#Обработчик кнопки добавить машину
@dp.message(lambda message: message.text == buttons.btn_add_car.text)
async def admin_add_car(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    user_id = message.from_user.id
    admin_car_step[user_id] = 1
    admin_car_data[user_id] = {}
    await message.answer(
        "Шаг 1 из 9: \n"
        "Марка машины:",
        reply_markup=dur_reg_keyboard
    )

#Обработчик сообщений для админ-добавления
async def handle_add_car(message: types.Message,user_id: int):
    if user_id not in admin_car_step:
        return
    step = admin_car_step[user_id]
    if step == 1:
        admin_car_data[user_id]['brand'] = message.text
        admin_car_step[user_id] = 2
        await message.answer(
            "Шаг 2 из 9: \n"
            "Модель машины:",
            reply_markup=dur_reg_keyboard
        )
    elif step == 2:
        admin_car_data[user_id]['model'] = message.text
        admin_car_step[user_id] = 3
        await message.answer(
            "Шаг 3 из 9: \n"
            "Год машины:",
            reply_markup=dur_reg_keyboard
        )
    elif step == 3:
        admin_car_data[user_id]['year'] = message.text
        admin_car_step[user_id] = 4
        await message.answer(
            "Шаг 4 из 9: \n"
            "Леворульная/Праворульная:",
            reply_markup=dur_reg_keyboard
        )
    elif step == 4:
        admin_car_data[user_id]['steering_wheel'] = message.text
        admin_car_step[user_id] = 5
        await message.answer(
            "Шаг 5 из 9: \n"
            "Механика/Автомат/Робот:",
            reply_markup=dur_reg_keyboard
        )
    elif step == 5:
        admin_car_data[user_id]['transmission'] = message.text
        admin_car_step[user_id] = 6
        await message.answer(
            "Шаг 6 из 9: \n"
            "Цвет машины:",
            reply_markup=dur_reg_keyboard
        )
    elif step == 6:
        admin_car_data[user_id]['color'] = message.text
        admin_car_step[user_id] = 7
        await message.answer(
            "Шаг 7 из 9: \n"
            "Объем двигателя машины:",
            reply_markup=dur_reg_keyboard
        )
    elif step == 7:
        admin_car_data[user_id]['engine_volume'] = message.text
        admin_car_step[user_id] = 8
        await message.answer(
            "Шаг 8 из 9: \n"
            "Цена за 1 день аренды:",
            reply_markup=dur_reg_keyboard
        )
    elif step == 8:
        admin_car_data[user_id]['price_per_day'] = message.text
        admin_car_step[user_id] = 9
        await message.answer(
            "Шаг 9 из 9: \n"
            "Фото машины:",
            reply_markup=dur_reg_keyboard
        )
    elif step == 9:
        print(f"Шаг 9: получил сообщение, тип: {message.content_type}")
        print(f"Есть фото: {bool(message.photo)}")
        if message.photo:
            print(f"Количество фото: {len(message.photo)}")
            admin_car_data[user_id]['photo_id'] = message.photo[-1].file_id
            database.add_car(
                admin_car_data[user_id]['brand'],
                admin_car_data[user_id]['model'],
                admin_car_data[user_id]['year'],
                admin_car_data[user_id]['steering_wheel'],
                admin_car_data[user_id]['transmission'],
                admin_car_data[user_id]['color'],
                admin_car_data[user_id]['engine_volume'],
                admin_car_data[user_id]['price_per_day'],
                admin_car_data[user_id]['photo_id']
            )
            del admin_car_step[user_id]
            del admin_car_data[user_id]
            await message.answer(
                "Машина успешно добавлена!",
                reply_markup=admin_cars_keyboard
            )
        else:
            await message.answer(
                "Пожалуйста, отправьте фото машины:",
                reply_markup=dur_reg_keyboard
                )

#Обработчик кнопки Удалить машину (админ)
@dp.message(lambda message: message.text == buttons.btn_delete_car.text)
async def admin_delete_car(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    cars = database.get_all_cars()
    if not cars:
        await message.answer('В базе нет машин')
        return
    car_btns = []
    for car in cars:
        car_btns.append([KeyboardButton(text=f"{car['brand']} {car['model']}")])
    car_btns.append([buttons.btn_back_to_admin])
    cars_keyboard = ReplyKeyboardMarkup(
        keyboard=car_btns,  # ← исправлено
        resize_keyboard=True
    )
    await message.answer(
        "Выберите машину для удаления:",
        reply_markup=cars_keyboard
    )

#Подтверждение удаления
@dp.message(lambda message: message.text and message.from_user.id == ADMIN_ID)
async def confirm_delete_car(message: types.Message):
    if message.text == buttons.btn_back_to_admin.text:
        return
    car_name = message.text
    cars = database.get_all_cars()
    selected_car = None
    for car in cars:
        if f"{car['brand']} {car['model']}" == car_name:
            selected_car = car
            break
    if not selected_car:
        await message.answer('Машина не найдена')
        return
    user_id = message.from_user.id
    admin_delete_car_id[user_id] = selected_car['car_id']

    confirm_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да, удалить", callback_data="confirm_delete")],
            [InlineKeyboardButton(text="Нет, отмена", callback_data="cancel_delete")]
        ]
    )
    await message.answer(
        f"Вы уверены, что хотите удалить машину {selected_car['brand']} {selected_car['model']}?",
        reply_markup=confirm_keyboard
    )
#Обработчик подтверждения удаления
@dp.callback_query(lambda c: c.data == 'confirm_delete')
async def confirm_delete_car(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if user_id not in admin_delete_car_id:
        await callback.message.edit_text("Ошибка: машина не выбрана")
        return
    car_id = admin_delete_car_id[user_id]
    res = database.delete_car(car_id)

    if res:
        await callback.message.edit_text('Машина успешно удалена')
    else:
        await callback.message.edit_text('Ошибка при удаление машины')
    
    del admin_delete_car_id[user_id]
    await callback.message.answer(
        'Управление машинами:',
        reply_markup=admin_cars_keyboard
    )

#Обработчик отмены удаления
@dp.callback_query(lambda c: c.data == "cancel_delete")
async def cancel_delete_car(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if user_id in admin_delete_car_id:
        del admin_delete_car_id[user_id]
    await callback.message.edit_text("Удаление отменено")
    await callback.message.answer(
        "Управление машинами:",
        reply_markup=admin_cars_keyboard
    )


#   |

#Обработчик кнопки регистрации
@dp.message(lambda message: message.text == buttons.btn_reg.text)
async def start_reg(message: types.Message):
    user_id = message.from_user.id
    if user_id in booking_step:
        del booking_step[user_id]
    if user_id in booking_data:
        del booking_data[user_id]
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
    elif user_id in admin_car_step:
        if admin_car_step[user_id] > 1:
            admin_car_step[user_id] -= 1
            await callback.message.delete()
            await callback.message.answer(f"Шаг {admin_car_step[user_id]} из 9. Повторите ввод:")
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
    elif user_id in admin_car_step:
        del admin_car_step[user_id]
        del admin_car_data[user_id]
        await callback.message.answer('Добавление машины отменено',reply_markup=admin_cars_keyboard)


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
        await callback.message.answer(
            "Регистрация почти завершена!\n\n"
            "Для бронирования автомобилей потребуются:\n"
            "1. Фото первой страницы паспорта\n"
            "2. Фото водительского удостоверения\n\n"
            "Загрузить сейчас или позже?",
            reply_markup=documents_choice_keyboard
        )
        temp_client_photos[user_id] = {'step': 1}

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



#Обработчик кнопки документов загрузить сейчас
@dp.callback_query(lambda c: c.data == "upload_now")
async def upload_now(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if user_id not in temp_client_photos:
        await callback.message.answer("Вы уже завершили регистрацию")
        return
    temp_client_photos[user_id] = {'step': 1}
    back_to_choice_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="back_to_doc_choice")]
    ]
    )
    await callback.message.edit_text(
        "Шаг 1 из 2: Отправьте фото первой страницы паспорта",
        reply_markup = back_to_choice_keyboard
    )

#Обработчик кнопки возврата на выбор сейчас/позже
@dp.callback_query(lambda c: c.data == "back_to_doc_choice")
async def back_to_doc_choice(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    temp_client_photos[user_id] = {'step': 1}
    await callback.message.edit_text(
        "Для бронирования автомобиля потребуются:\n"
        "1. Фото первой страницы паспорта\n"
        "2. Фото водительского удостоверения\n\n"
        "Загрузить сейчас или позже?",
        reply_markup=documents_choice_keyboard
    )

#Обработчки кнопки документов загрузить позже 
@dp.callback_query(lambda c: c.data == "upload_later")
async def upload_later(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    await callback.message.edit_text(
        "Регистрация завершена!\n"
        "Вы сможете загрузить документы во время бронирования машины"
    )
    await callback.message.answer(
        "Главное меню:",
        reply_markup=reg_keyboard
    )
    if user_id in temp_client_photos:
        del temp_client_photos[user_id]

#Обработчик получения фото
@dp.message(lambda message: message.photo and message.from_user.id in temp_client_photos)
async def handle_document_photo(message: types.Message):
    user_id = message.from_user.id
    step = temp_client_photos[user_id].get('step', 1)
    
    back_to_passport_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="back_to_passport")]
        ]
    )
    
    if step == 1:
        temp_client_photos[user_id]['passport'] = message.photo[-1].file_id
        temp_client_photos[user_id]['step'] = 2
        await message.answer(
            "Шаг 2 из 2: Отправьте фото водительского удостоверения",
            reply_markup = back_to_passport_keyboard
        )
    elif step == 2:
        temp_client_photos[user_id]['license'] = message.photo[-1].file_id
        temp_client_photos[user_id]['step'] = 3
        print(f"DEBUG: step установлен в {temp_client_photos[user_id]['step']}")
        confirm_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Да, всё верно", callback_data="confirm_documents")],
                [InlineKeyboardButton(text="Отправить заново", callback_data="back_to_passport")]
            ]
        )
        print(f"DEBUG: step={step}, отправлена клавиатура подтверждения")
        await message.answer(
            "Фото получены!\n\n"
            "Убедитесь в правильности фото!",
            reply_markup=confirm_keyboard
        )

#обработчик подтверждения
@dp.callback_query(lambda c: c.data == "confirm_documents")
async def confirm_documents(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    
    if user_id not in temp_client_photos:
        await callback.message.answer("Ошибка. Попробуйте заново")
        return
    
    if 'passport' not in temp_client_photos[user_id] or 'license' not in temp_client_photos[user_id]:
        await callback.message.answer("Ошибка: не все фото получены")
        return

    database.update_client_documents(
        user_id,
        temp_client_photos[user_id]['passport'],
        temp_client_photos[user_id]['license']
    )
    
    await callback.message.delete()
    await callback.message.answer(
    "Спасибо! Документы сохранены.\n"
    "Теперь вы можете бронировать автомобили.",
    reply_markup=reg_keyboard
)
    del temp_client_photos[user_id]

#Обработчик возврата к паспорту кнопка назад
@dp.callback_query(lambda c: c.data == "back_to_passport")
async def back_to_passport(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if user_id not in temp_client_photos:
        await callback.message.answer("Ошибка")
        return

    temp_client_photos[user_id]['step'] = 1
    back_to_choice_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="back_to_doc_choice")]
        ]
    )
    await callback.message.edit_text(
        "Шаг 1 из 2: Отправьте фото первой страницы паспорта",
        reply_markup=back_to_choice_keyboard
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

#Обработчик кнопки весь автопарк (клиент)
@dp.message(lambda message: message.text == buttons.btn_show_cars.text)
async def show_cars_for_client(message: types.Message):
    cars = database.get_all_cars()
    if not cars:
        await message.answer("Машины отсутствуют")
        return
    car_buttons = []
    for car in cars:
        car_buttons.append([KeyboardButton(text=f"{car['brand']} {car['model']}")])
    car_buttons.append([KeyboardButton(text="Назад")])
    cars_keyboard = ReplyKeyboardMarkup(
        keyboard=car_buttons,
        resize_keyboard=True
    )
    await message.answer(
        "Все машины:",
        reply_markup=cars_keyboard
    )



#Обработчик выбора машины и показа харак-ик (клиент)
@dp.message(lambda message: message.text and 
    message.from_user.id not in registration_step and
    message.from_user.id not in booking_step and
    message.from_user.id not in admin_car_step and
    message.text not in ['Весь автопарк', 'Забронировать машину', 'Мои бронирования', 'Помощь', 'Назад', 'Список всех машин', 'Управление машинами', 'Все бронирования', 'Добавить машину', 'Удалить машину'])
async def show_car_details(message: types.Message):
    print(f"=== show_car_details ВЫЗВАНА для {message.text} ===")
    # Убираем проверку на админа
    # if message.from_user.id != ADMIN_ID:
    #     return
    
    user_id = message.from_user.id 
    car_text = message.text
    brand_model_list = car_text.split(' ', 1)
    if len(brand_model_list) < 2:
        return
    
    brand, model = brand_model_list[0], brand_model_list[1]
    cars = database.get_all_cars()
    selected_car = None
    for car in cars:
        if car['brand'] == brand and car['model'] == model:
            selected_car = car
            break
    
    if not selected_car:
        await message.answer('Машина не найдена')
        return
    
    text = f"""
*{selected_car['brand']} {selected_car['model']}*
Год: {selected_car['year']}
Цена: {selected_car['price_per_day']}₽/день
Руль: {selected_car['steering_wheel']}
Коробка: {selected_car['transmission']}
Цвет: {selected_car['color']}
Объем: {selected_car['engine_volume']} л
"""
    if selected_car['photo_id']:
        await message.answer_photo(
            selected_car['photo_id'],
            caption=text,
            parse_mode='Markdown'
        )
    else:
        await message.answer(text, parse_mode='Markdown')
    
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
    client = database.get_client_by_tgid(user_id)

    if not client:
        await message.answer("Сначала зарегистрируйтесь!")
        return
    
    if client['documents_uploaded'] != 1:
        no_docs_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Загрузить документы", callback_data="upload_docs_now")],
                [InlineKeyboardButton(text="Не загружать", callback_data="cancel_booking_docs")]
            ]
        )
        await message.answer(
            "Для бронирования автомобиля необходимо загрузить фото паспорта и водительского удостоверения.\n\n"
            "Загрузить документы сейчас?",
            reply_markup=no_docs_keyboard
        )
        return
    await message.answer(
        "Выберите вариант аренды:",
        reply_markup=indefinite_keyboard
    )

#Обработчики выбора срока (определенное кол-во дней и неопределенное)
@dp.callback_query(lambda c: c.data == "enter_days")
async def enter_days(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    booking_step[user_id] = "waiting_days"
    booking_data[user_id] = {}
    await callback.message.edit_text(
        "Введите количество дней аренды:",
        reply_markup=dur_reg_keyboard2
    )

@dp.callback_query(lambda c: c.data == "indefinite_rent")
async def indefinite_rent(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    booking_step[user_id] = "waiting_start_date_indefinite"
    booking_data[user_id] = {'indefinite': True}
    await callback.message.edit_text(
        "Введите ДАТУ НАЧАЛА аренды в формате ДД.ММ.ГГГГ",
        reply_markup=dur_reg_keyboard
    )


#Обработчик кнопки выбора upload_docs_now
@dp.callback_query(lambda c: c.data == "upload_docs_now")
async def upload_docs_now(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    temp_client_photos[user_id] = {'step': 1}
    back_to_choice_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="back_to_doc_choice")]
    ]
    )
    await callback.message.edit_text(
        "Шаг 1 из 2: Отправьте фото первой страницы паспорта",
        reply_markup = back_to_choice_keyboard
    )
#Обработчик кнопки выбора cancel_booking_docs
@dp.callback_query(lambda c: c.data == "cancel_booking_docs")
async def cancel_booking_docs(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "Бронирование отменено.\n"
        "Для бронирования машин требуется загрузка документов."
    )
    await callback.message.answer(
        "Главное меню:",
        reply_markup=reg_keyboard
    )



    # booking_step[user_id] = "waiting_start_date"
    # booking_data[user_id] = {}
    # await message.answer("Введите дату и время желаемой даты аренды в формате - ДД.ММ.ГГГГ ЧЧ:ММ\n" \
    # "Пример: 11.11.2011 11:11"
    #                     ,reply_markup=dur_reg_keyboard)


#Функция перехода к доступным машинам
async def proceed_to_available_cars(message: types.Message, user_id: int, indefinite: bool):
    # Устанавливаем шаг ДО начала обработки
    booking_step[user_id] = "waiting_car_choice"
    print(f"DEBUG: установлен step = waiting_car_choice для {user_id}")
    
    if indefinite:
        start = booking_data[user_id]['start_date'] + " 00:00"
        far_future = (datetime.strptime(booking_data[user_id]['start_date'], '%d.%m.%Y') + timedelta(days=3650)).strftime('%d.%m.%Y') + " 23:59"
        available_cars = database.get_avilable_cars(start, far_future)
        price_info = "Оплата обсуждается при встрече"
    else:
        start = booking_data[user_id]['start_date'] + " 00:00"
        end = booking_data[user_id]['end_date'] + " 23:59"
        available_cars = database.get_avilable_cars(start, end)
        total_days = (datetime.strptime(booking_data[user_id]['end_date'], '%d.%m.%Y') - datetime.strptime(booking_data[user_id]['start_date'], '%d.%m.%Y')).days
        price_info = "Примерная стоимость будет рассчитана после выбора авто"
    
    if not available_cars:
        await message.answer("Нет свободных машин на выбранные даты")
        del booking_step[user_id], booking_data[user_id]
        return
    
    # Reply-кнопки с машинами
    car_buttons = []
    for car in available_cars:
        car_buttons.append([KeyboardButton(text=f"{car['brand']} {car['model']}")])
    
    keyboard = ReplyKeyboardMarkup(keyboard=car_buttons, resize_keyboard=True)
    
    cancel_inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отменить бронирование", callback_data="cancel_booking")]
        ]
    )
    
    await message.answer(
        f"Доступные машины на выбранные даты\n{price_info}\n\n"
        "Нажмите на машину, чтобы узнать подробности и подтвердить бронь:",
        reply_markup=keyboard
    )
    
    await message.answer(
        "Кнопка отмены брони",
        reply_markup=cancel_inline
    )
    
    # Еще раз убеждаемся, что шаг установлен
    booking_step[user_id] = "waiting_car_choice"
    print(f"DEBUG: ЕЩЕ РАЗ установлен step = waiting_car_choice для {user_id}")

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
async def handle_booking_message(message: types.Message, user_id: int):
    # step = booking_step[user_id]
    step = booking_step.get(user_id)  # используй .get, чтобы избежать KeyError
    print(f"DEBUG: step = {step}, text = '{message.text}'")  # ← вот эту строку
    if step == "waiting_choice":
        if user_id in booking_data:
            del booking_data[user_id]
        await message.answer(
            "Выберите вариант аренды:",
            reply_markup=indefinite_keyboard
        )
        del booking_step[user_id]
        return
    
    if step == 'waiting_days':
        try:
            days = int(message.text)
            if days < 1:
                await message.answer("Количество дней должно быть больше 0.")
                return
            if days > 30:
                await message.answer("Максимум 30 дней. Введите меньше:")
                return

            booking_data[user_id]['days'] = days
            booking_step[user_id] = "waiting_start_date"
            await message.answer(
                f"{days} день (дней).\nТеперь введите желаемую дату начала аренды в формате ДД.ММ.ГГГГ:",
                reply_markup=dur_reg_keyboard2
            )
        except ValueError:
            await message.answer("Введите целое число дней цифрами")
    
    elif step == 'waiting_start_date_indefinite':
        try:
            start_date = datetime.strptime(message.text, '%d.%m.%Y')
            if start_date < datetime.now():
                await message.answer("Дата не может быть в прошлом")
                return
            booking_data[user_id]['start_date'] = message.text
            booking_data[user_id]['indefinite'] = True
            await proceed_to_available_cars(message, user_id, indefinite=True)
        except ValueError:
            await message.answer("Неверный формат. Введите ДД.ММ.ГГГГ")
    
    elif step == 'waiting_start_date':
        # Проверяем, не выбрал ли пользователь машину (если step не обновился)
        car_names = [f"{car['brand']} {car['model']}" for car in database.get_all_cars()]
        if message.text in car_names:
            # Вызываем функцию обработки выбора машины
            await handle_car_choice(message, user_id, message.text)
            return
        else:
            # нормальная обработка даты
            try:
                start_date = datetime.strptime(message.text, '%d.%m.%Y')
                if start_date < datetime.now():
                    await message.answer("Дата не может быть в прошлом")
                    return
                booking_data[user_id]['start_date'] = message.text
                days = booking_data[user_id]['days']
                end_date = start_date + timedelta(days=days)
                booking_data[user_id]['end_date'] = end_date.strftime('%d.%m.%Y')
                await proceed_to_available_cars(message, user_id, indefinite=False)
            except ValueError:
                await message.answer("Неверный формат даты")
    elif step == "waiting_car_choice":
        car_name = message.text
        
        if car_name == 'Назад':
            booking_step[user_id] = "waiting_choice"
            await message.answer("Выберите вариант аренды:", reply_markup=indefinite_keyboard)
            return

        # Поиск выбранной машины
        cars = database.get_all_cars()
        selected_car = None
        for car in cars:
            if f"{car['brand']} {car['model']}" == car_name:
                selected_car = car
                break
        
        if not selected_car:
            await message.answer("Машина не найдена. Попробуйте снова.")
            return
        
        booking_data[user_id]['car_id'] = selected_car['car_id']
        
        text = f"""
*{selected_car['brand']} {selected_car['model']}*
Год: {selected_car['year']}
Цена: {selected_car['price_per_day']}₽/день
Руль: {selected_car['steering_wheel']}
Коробка: {selected_car['transmission']}
Цвет: {selected_car['color']}
Объем: {selected_car['engine_volume']} л
"""     
        if 'indefinite' in booking_data[user_id] and booking_data[user_id]['indefinite']:
            total_price_text = f"Процесс оплаты обсуждается при встрече\nЦена за один день {selected_car['price_per_day']}₽"
            days_text = 'Срок не определен'
        else:
            days = booking_data[user_id]['days']
            total_price = selected_car['price_per_day'] * days
            booking_data[user_id]['total_price'] = total_price
            total_price_text = f"Итого: {total_price}₽"
            days_text = f"{days} день/дня/дней"
        
        confirm_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Подтвердить бронь", callback_data="confirm_booking")],
                [InlineKeyboardButton(text="Отменить", callback_data="cancel_booking")]
            ]
        )
        
        if selected_car['photo_id']:
            await message.answer_photo(
                selected_car['photo_id'],
                caption=f"{text}\n{days_text}\n{total_price_text}\n\nПодтверждаете бронирование?",
                parse_mode='Markdown',
                reply_markup=confirm_keyboard
            )
        else:
            await message.answer(
                f"{text}\n📆 {days_text}\n{total_price_text}\n\nПодтверждаете бронирование?",
                parse_mode='Markdown',
                reply_markup=confirm_keyboard
            )
        booking_step[user_id] = "waiting_confirm"
            
#Обработчики inline-кнопок подтверждения/отмены
@dp.callback_query(lambda c: c.data == "confirm_booking")
async def confirm_booking(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    
    if user_id not in booking_step or booking_step[user_id] != "waiting_confirm":
        await callback.message.answer("Ошибка. Попробуйте начать бронирование заново.")
        return
    
    # Удаляем сообщение с фото и кнопками
    await callback.message.delete()
    
    # Заглушка условий аренды
    terms_text = """
*Условия аренды:*

<ПОКА ПУСТО>
"""
    
    final_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Подтверждаю", callback_data="final_confirm")],
            [InlineKeyboardButton(text="Отказываюсь", callback_data="cancel_booking")]
        ]
    )
    
    # Отправляем НОВОЕ сообщение (не редактируем удалённое)
    await callback.message.answer(
        terms_text,
        parse_mode='Markdown',
        reply_markup=final_keyboard
    )
    booking_step[user_id] = "waiting_final_confirm"

#Подтверждение брони
@dp.callback_query(lambda c: c.data == "final_confirm")
async def final_confirm_booking(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    
    if user_id not in booking_data:
        await callback.message.answer("Ошибка. Бронь не найдена.")
        return
    client = database.get_client_by_tgid(user_id)
    if not client:
        await callback.message.answer("Ошибка: клиент не найден")
        return
    
    client_id = client['client_id']
    
    if 'indefinite' in booking_data[user_id] and booking_data[user_id]['indefinite']:
        end_date = "31.12.2099"
        total_cost = 0
    else:
        end_date = booking_data[user_id]['end_date']
        total_cost = booking_data[user_id]['total_price']
    
    booking_id = database.add_booking(
        booking_data[user_id]['car_id'],
        client_id,
        booking_data[user_id]['start_date'],
        end_date,
        total_cost,
        'pending'
    )
    
    await callback.message.edit_text(
        "Заявка на бронирование успешно отправлена!\n"
        "Статус: 🟡 На рассмотрении.\n\n"
        "Вам поступит ответ в ближайшее время."
    )
    await callback.message.answer(
        "Главное меню:",
        reply_markup=reg_keyboard
    )
    

    del booking_step[user_id]
    del booking_data[user_id]
    
    # уведомление админу (позже)

#Отмена брони
@dp.callback_query(lambda c: c.data == "cancel_booking")
async def cancel_booking(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    await callback.message.delete()
    await callback.message.answer(
        "Бронирование отменено",
        reply_markup=reg_keyboard
    )
    if user_id in booking_step:
        del booking_step[user_id]
    if user_id in booking_data:
        del booking_data[user_id]



@dp.message()
async def handle_all_messages(message: types.Message):
    user_id = message.from_user.id
    print(f"=== handle_all_messages: текст '{message.text}', user_id={user_id}")  # ← добавить
    print(f"booking_step: {booking_step}")
    if user_id in booking_step:
        print("→ Переход в handle_booking_message")
        await handle_booking_message(message, user_id)
    elif user_id in registration_step:
        print("→ Переход в handle_registration_message")
        await handle_registration_message(message, user_id)
    elif user_id in admin_car_step:
        print("→ Переход в handle_add_car")
        await handle_add_car(message, user_id)
    else:
        print("→ Ни одно состояние не подошло")
        await message.answer('Используйте кнопки в меню.')


async def main():
    print("Бот запущен!")
    await dp.start_polling(bot) 

if __name__ == "__main__":
    asyncio.run(main())

