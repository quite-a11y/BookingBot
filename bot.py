import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup,KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from datetime import datetime, timedelta
import database
import buttons

with open('api.txt','r',encoding='utf-8') as r:
    line = r.read()
    print(line)

#journalctl -u valera_bot -f
#systemctl restart valera_bot
TOKEN = line
bot = Bot(token=TOKEN)
dp = Dispatcher()
ADMIN_ID = 1027977984
#/
#Фэйковый
# ADMIN_ID = 1027977985
#/
user_data = {}
booking_data = {}
registration_step = {} #Отслеживание шагов регистрации
booking_step = {} #Отслеживание шагов бронирования
admin_car_data = {}
admin_car_step = {}
admin_last_car_message = {}
admin_delete_car_id = {}
temp_client_photos = {}  # {user_id: {'step': 1, 'passport': None, 'license': None}}
# Добавь рядом с другими словарями в начале python.py:
admin_temp_data = {}  # {user_id: {'status': 'pending'|'confirmed', 'client_name': '...', ...}}

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
# @dp.message(lambda message: message.text == "Назад")
# async def back_to_main_menu(message: types.Message):
#     print(f"DEBUG back_to_main_menu: {message.text}")
#     user_id = message.from_user.id
    
#     if user_id == ADMIN_ID:
#         await message.answer(
#             "Админ панель:",
#             reply_markup=admin_main_keyboard
#         )
#     else:
#         await message.answer(
#             "Главное меню:",
#             reply_markup=reg_keyboard
#         )
#Обработчик кнопки все машины у админа
@dp.message(lambda message: message.text == buttons.btn_admin_all_cars.text)
async def admin_show_all_cars(message: types.Message):
    print(f"DEBUG admin_show_all_cars: {message.text}")
    if message.from_user.id != ADMIN_ID:
        return
    
    cars = database.get_all_cars()
    if not cars:
        await message.answer('В базе нет машин')
        return
    cars_buttons = []
    for car in cars:
        cars_buttons.append([KeyboardButton(text=f"{car['brand']} {car['model']}")])
    cars_buttons.append([KeyboardButton(text="🔙 Назад")])
    cars_keyboard = ReplyKeyboardMarkup(
        keyboard=cars_buttons,
        resize_keyboard=True
    )
    
    # Флаг: админ смотрит все машины из управления машинами
    admin_temp_data[message.from_user.id] = {'viewing_all_cars': True}
    
    await message.answer(
        "Список всех машин:",
        reply_markup=cars_keyboard
    )

#Обработчик кнопки старт
@dp.message(lambda message: message.text == buttons.btn_start.text)
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    
    if user_id == ADMIN_ID:
        await message.answer(
            f"Админ кнопки: '{buttons.btn_admin_cars.text}' и '{buttons.btn_admin_all_bookings.text}'",
        reply_markup=admin_main_keyboard
        )
        return
    
    # Проверяем, зарегистрирован ли обычный пользователь
    client = database.get_client_by_tgid(user_id)
    if client:
        await message.answer(
            f'С возвращением, {client["full_name"]}!',
            reply_markup=reg_keyboard
        )
    else:
        await message.answer(
            f'Привет, {message.from_user.first_name}!\n'
            'Для регистрации нажми кнопку ниже.', 
            reply_markup=unreg_keyboard
        )
#Все бронирования (админ)
@dp.message(lambda message: message.text == buttons.btn_admin_all_bookings.text)
async def admin_all_bookings(message: types.Message):
    print("DEBUG: admin_all_bookings сработал!")
    if message.from_user.id != ADMIN_ID:
        return
    
    bookings = database.get_all_bookings_with_details()
    
    pending_count = len([b for b in bookings if b['status'] == 'pending'])
    confirmed_count = len([b for b in bookings if b['status'] == 'confirmed'])
    
    status_buttons = []
    if pending_count > 0:
        status_buttons.append([KeyboardButton(text=f"🟡 Ожидают подтверждения ({pending_count})")])
    if confirmed_count > 0:
        status_buttons.append([KeyboardButton(text=f"🟢 Ожидают встречи ({confirmed_count})")])
    
    status_buttons.append([KeyboardButton(text="🔙 Назад")])
    
    status_keyboard = ReplyKeyboardMarkup(
        keyboard=status_buttons,
        resize_keyboard=True
    )
    
    await message.answer(
        "Выберите статус для просмотра:",
        reply_markup=status_keyboard
    )
# обработчик выбора статуса 
@dp.message(lambda message: message.text and 
    message.from_user.id == ADMIN_ID and 
    (message.text.startswith("🟡") or message.text.startswith("🟢")))
async def admin_status_choice(message: types.Message):
    print(f"DEBUG admin_status_choice: {message.text}")
    
    if message.text.startswith("🟡"):
        status = 'pending'
    elif message.text.startswith("🟢"):
        status = 'confirmed'
    else:
        return
    
    bookings = database.get_all_bookings_with_details()
    filtered = [b for b in bookings if b['status'] == status]
    
    if not filtered:
        await message.answer(f"Нет броней с этим статусом")
        return
    
    # Получаем уникальных клиентов
    unique_clients = {}
    for b in filtered:
        client_id = b['client_id']
        if client_id not in unique_clients:
            unique_clients[client_id] = b['full_name']
    
    client_buttons = []
    for client_id, full_name in unique_clients.items():
        client_buttons.append([KeyboardButton(text=f"👤 {full_name}")])
    
    client_buttons.append([KeyboardButton(text="🔙 Назад")])
    
    client_keyboard = ReplyKeyboardMarkup(
        keyboard=client_buttons,
        resize_keyboard=True
    )
    
    # Сохраняем выбранный статус для использования на следующих шагах
    admin_temp_data[message.from_user.id] = {'status': status}
    
    status_text = "ожидают подтверждения" if status == 'pending' else "ожидают встречи"
    await message.answer(
        f"Клиенты, у которых есть брони со статусом '{status_text}':",
        reply_markup=client_keyboard
    )

#Обработчик выбора клиента
@dp.message(lambda message: message.text and 
    message.from_user.id == ADMIN_ID and 
    message.text.startswith("👤"))
async def admin_client_choice(message: types.Message):
    print(f"DEBUG admin_client_choice: {message.text}")
    
    user_id = message.from_user.id
    if user_id not in admin_temp_data or 'status' not in admin_temp_data[user_id]:
        await message.answer("Ошибка: не выбран статус")
        return
    
    status = admin_temp_data[user_id]['status']
    full_name = message.text[2:]  # убираем "👤 "
    
    bookings = database.get_all_bookings_with_details()
    client_bookings = [b for b in bookings if b['status'] == status and b['full_name'] == full_name]
    
    if not client_bookings:
        await message.answer("Брони не найдены")
        return
    
    booking_buttons = []
    for b in client_bookings:
        btn_text = f"{b['brand']} {b['model']} | {b['start_date']}"
        booking_buttons.append([KeyboardButton(text=btn_text)])
    
    booking_buttons.append([KeyboardButton(text="🔙 Назад")])
    
    booking_keyboard = ReplyKeyboardMarkup(
        keyboard=booking_buttons,
        resize_keyboard=True
    )
    
    # Сохраняем имя клиента для возврата назад
    admin_temp_data[user_id]['client_name'] = full_name
    admin_temp_data[user_id]['at_clients_level'] = False
    
    status_text = "ожидают подтверждения" if status == 'pending' else "ожидают встречи"
    await message.answer(
        f"Брони клиента {full_name} ({status_text}):",
        reply_markup=booking_keyboard
    )

# Обработчик выбора конкретной брони (НОВЫЙ — 2 части: brand model | start_date)
@dp.message(lambda message: message.text and 
    message.from_user.id == ADMIN_ID and 
    " | " in message.text and 
    "  |  " not in message.text and  # исключаем старый формат с тремя частями
    not message.text.startswith("🟡") and 
    not message.text.startswith("🟢") and 
    not message.text.startswith("🔴") and
    not message.text.startswith("👤"))
async def admin_booking_details(message: types.Message):
    print(f"DEBUG admin_booking_details NEW: текст = '{message.text}'")
    
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return
    
    # Получаем статус из сохраненных данных
    if user_id not in admin_temp_data or 'status' not in admin_temp_data[user_id]:
        await message.answer("Ошибка: начните заново с 'Все бронирования'")
        return
    
    status = admin_temp_data[user_id]['status']
    
    parts = message.text.split(' | ')
    if len(parts) != 2:
        await message.answer("Ошибка формата. Ожидается: Марка Модель | дата")
        return
    
    car_info = parts[0].strip()
    start_date = parts[1].strip()
    
    bookings = database.get_all_bookings_with_details()
    selected_booking = None
    for b in bookings:
        if (b['status'] == status and 
            f"{b['brand']} {b['model']}" == car_info and 
            b['start_date'] == start_date):
            selected_booking = b
            break
    
    if not selected_booking:
        await message.answer("Бронь не найдена")
        return
    
    status_emoji = {'pending': '🟡', 'confirmed': '🟢', 'cancelled': '🔴'}.get(selected_booking['status'], '⚪')
    status_text = {'pending': 'Ожидает', 'confirmed': 'Подтверждено', 'cancelled': 'Отменено'}.get(selected_booking['status'], 'Неизвестно')
    
    # Форматируем даты из YYYY-MM-DD в DD.MM.YYYY
    start_display = selected_booking['start_date']
    end_display = selected_booking['end_date']
    try:
        if ' ' in start_display:
            dt = datetime.strptime(start_display.split(' ')[0], '%Y-%m-%d')
            start_display = dt.strftime('%d.%m.%Y')
        if ' ' in end_display:
            dt = datetime.strptime(end_display.split(' ')[0], '%Y-%m-%d')
            end_display = dt.strftime('%d.%m.%Y')
    except:
        pass
    
    text = f"""
{status_emoji} *Бронирование #{selected_booking['rental_id']}*

👤 Клиент: {selected_booking['full_name']}
📞 Телефон: {selected_booking['phone']}
📄 Паспорт: {selected_booking['passport_series']} {selected_booking['passport_number']}

🚗 Машина: {selected_booking['brand']} {selected_booking['model']}
💰 Цена: {selected_booking['price_per_day']}₽/день

📅 Дата начала: {start_display}
📅 Дата окончания: {end_display}
💵 Итого: {selected_booking['total_cost']}₽

📊 Статус: {status_text}
"""
    
    action_buttons = []
    if selected_booking['status'] == 'pending':
        action_buttons.append([
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"admin_confirm_{selected_booking['rental_id']}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_cancel_{selected_booking['rental_id']}")
        ])
    elif selected_booking['status'] == 'confirmed':
        action_buttons.append([
            InlineKeyboardButton(text="📝 Договор", callback_data=f"contract_{selected_booking['rental_id']}"),
            InlineKeyboardButton(text="❌ Отменить", callback_data=f"admin_cancel_{selected_booking['rental_id']}")
        ])
    
    # Контакты — передаём telegram_id клиента
    action_buttons.append([InlineKeyboardButton(text="📞 Контакты", callback_data=f"admin_contact_{selected_booking['telegram_id']}")])
    action_buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_to_bookings")])
    
    action_keyboard = InlineKeyboardMarkup(inline_keyboard=action_buttons)
    
    # Отправляем фото
    car_photo = selected_booking['photo_id']
    passport_photo = selected_booking['passport_photo_id']
    license_photo = selected_booking['driver_license_photo_id']
    
    media_group = []
    if car_photo:
        media_group.append(InputMediaPhoto(media=car_photo, caption=text[:1024], parse_mode='Markdown'))
    if passport_photo:
        media_group.append(InputMediaPhoto(media=passport_photo))
    if license_photo:
        media_group.append(InputMediaPhoto(media=license_photo))
    
    if media_group:
        await message.answer_media_group(media=media_group)
        await message.answer("Действия с бронью:", reply_markup=action_keyboard)
    else:
        await message.answer(text, parse_mode='Markdown', reply_markup=action_keyboard)
    
    # Сохраняем ID брони для возврата
    admin_temp_data[user_id]['last_booking_id'] = selected_booking['rental_id']
    admin_temp_data[user_id]['last_status'] = status

#Подтверждение удаления
async def confirm_delete_car(message: types.Message):
    print(f"DEBUG confirm_delete_car: {message.text}")
    
    # Пропускаем ВСЕ админские кнопки
    admin_buttons = [
        buttons.btn_admin_cars.text,
        buttons.btn_add_car.text,
        buttons.btn_delete_car.text,
        buttons.btn_admin_all_cars.text,
        buttons.btn_admin_all_bookings.text,
        buttons.btn_back_to_admin.text,
        "🔙 Назад"
    ]
    if message.text in admin_buttons:
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

#Обработчик выбора машины и показа харак-ик (клиент)
@dp.message(lambda message: message.text and 
    message.from_user.id not in registration_step and
    message.from_user.id not in booking_step and
    message.from_user.id not in admin_car_step and
    not message.text.startswith(('👤', '🟡', '🟢', '🔙', '🔴')) and
    message.text not in ['Весь автопарк', 'Забронировать машину', 'Мои бронирования', 'Помощь', 'Назад', 'Список всех машин', 'Управление машинами', 'Все бронирования', 'Добавить машину', 'Удалить машину'])
async def show_car_details(message: types.Message):
    print(f"DEBUG show_car_details: user={message.from_user.id}, текст={message.text}")
    
    # Разрешаем админу смотреть, только если он в режиме просмотра всех машин
    if message.from_user.id == ADMIN_ID:
        if not admin_temp_data.get(message.from_user.id, {}).get('viewing_all_cars'):
            return
    
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





#Обработчик кнопки управление машинами
@dp.message(lambda message: message.text == buttons.btn_admin_cars.text)
async def admin_cars_menu(message: types.Message):
    print(f"DEBUG admin_cars_menu: {message.text}")
    if message.from_user.id != ADMIN_ID:
        return
    # Очищаем admin_temp_data при входе в управление машинами
    admin_temp_data.pop(message.from_user.id, None)
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
    admin_temp_data.pop(message.from_user.id, None) 
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
    admin_temp_data.pop(message.from_user.id, None)
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
@dp.message(lambda message: message.text == "Назад" or message.text == "🔙 Назад")
async def back_handler(message: types.Message):
    user_id = message.from_user.id
    
    # Сначала проверяем просмотр всех машин
    if user_id == ADMIN_ID and admin_temp_data.get(user_id, {}).get('viewing_all_cars'):
        del admin_temp_data[user_id]
        await message.answer("Управление машинами:", reply_markup=admin_cars_keyboard)
        return
    
    if user_id == ADMIN_ID and user_id in admin_temp_data:
        # Уровень 3: просмотр броней клиента → вернуться к списку клиентов
        if 'client_name' in admin_temp_data[user_id]:
            client_name = admin_temp_data[user_id].pop('client_name')
            status = admin_temp_data[user_id].get('status', 'pending')
            status_text = "ожидают подтверждения" if status == 'pending' else "ожидают встречи"
            
            bookings = database.get_all_bookings_with_details()
            
            filtered = [b for b in bookings if b['status'] == status]
            unique_clients = {}
            for b in filtered:
                client_id = b['client_id']
                if client_id not in unique_clients:
                    unique_clients[client_id] = b['full_name']
            
            client_buttons = []
            for client_id, full_name in unique_clients.items():
                client_buttons.append([KeyboardButton(text=f"👤 {full_name}")])
            client_buttons.append([KeyboardButton(text="🔙 Назад")])
            
            admin_temp_data[user_id]['at_clients_level'] = True
            
            client_keyboard = ReplyKeyboardMarkup(keyboard=client_buttons, resize_keyboard=True)
            await message.answer(
                f"Клиенты, у которых есть брони со статусом '{status_text}':",
                reply_markup=client_keyboard
            )
            return
        
        # Уровень 2: список клиентов → вернуться к выбору статуса
        if admin_temp_data[user_id].get('at_clients_level'):
            status = admin_temp_data[user_id].get('status', 'pending')
            
            bookings = database.get_all_bookings_with_details()
            pending_count = len([b for b in bookings if b['status'] == 'pending'])
            confirmed_count = len([b for b in bookings if b['status'] == 'confirmed'])
            
            status_buttons = []
            if pending_count > 0:
                status_buttons.append([KeyboardButton(text=f"🟡 Ожидают подтверждения ({pending_count})")])
            if confirmed_count > 0:
                status_buttons.append([KeyboardButton(text=f"🟢 Ожидают встречи ({confirmed_count})")])
            status_buttons.append([KeyboardButton(text="🔙 Назад")])
            
            admin_temp_data[user_id] = {'status': status}
            
            status_keyboard = ReplyKeyboardMarkup(keyboard=status_buttons, resize_keyboard=True)
            await message.answer(
                "Выберите статус для просмотра:",
                reply_markup=status_keyboard
            )
            return
        
        # Уровень 1: выбор статуса → вернуться в админ-панель
        del admin_temp_data[user_id]
        await message.answer("Админ панель:", reply_markup=admin_main_keyboard)
        return
    
    # Если админ нажал "Назад" но его нет в admin_temp_data
    if user_id == ADMIN_ID:
        await message.answer("Админ панель:", reply_markup=admin_main_keyboard)
        return
    
    # Для обычных пользователей
    await message.answer("Главное меню:", reply_markup=reg_keyboard)

# Заглушка для кнопки "Договор"
@dp.callback_query(lambda c: c.data.startswith("contract_"))
async def show_contract(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("📝 Раздел 'Договор' в разработке")

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
    print(f"DEBUG show_cars_for_client: {message.text}")
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
    car = database.get_car_by_id(booking_data[user_id]['car_id'])
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
    admin_text = f"""
НОВАЯ ЗАЯВКА НА БРОНИРОВАНИЕ!

Клиент: {client['full_name']}
Телефон: {client['phone']}
Паспорт: {client['passport_series']} {client['passport_number']}
Дата выдачи: {client['date_of_issue']}
Прописка: {client['registration']}

Машина: {car['brand']} {car['model']}
Год: {car['year']}
Коробка: {car['transmission']}
Руль: {car['steering_wheel']}
Цвет: {car['color']}
Объем: {car['engine_volume']} л

Дата начала: {booking_data[user_id]['start_date']}
Дата окончания: {end_date}
Стоимость: {total_cost}₽

Статус: 🟡 Ожидает подтверждения
"""
    car_photo = car['photo_id'] if car['photo_id'] else None

    passport_photo = client['passport_photo_id'] if client['passport_photo_id'] else None
    license_photo = client['driver_license_photo_id'] if client['driver_license_photo_id'] else None

    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Подтвердить", callback_data=f"admin_confirm_{booking_id}"),
                InlineKeyboardButton(text="Отклонить", callback_data=f"admin_cancel_{booking_id}")
            ],
            [InlineKeyboardButton(text="ЛС клиента", callback_data=f"admin_contact_{user_id}")]
        ]
    )

    media_group_photos = []
    if car_photo:
        media_group_photos.append(InputMediaPhoto(media=car_photo,caption=admin_text, parse_mode='Markdown'))
    if passport_photo:
        media_group_photos.append(InputMediaPhoto(media=passport_photo))
    if license_photo:
        media_group_photos.append(InputMediaPhoto(media=license_photo))

    if media_group_photos:
        await bot.send_media_group(chat_id=ADMIN_ID, media=media_group_photos)
    else:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode='Markdown', reply_markup=admin_keyboard)

    #Отдельное соо для клавиатуры
    if media_group_photos:
        await bot.send_message(chat_id=ADMIN_ID, text="Действия с заявкой:", reply_markup=admin_keyboard)

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

#Обработчики для админ-кнопок (подтвердить,отклонить, ЛС клиента)
@dp.callback_query(lambda c: c.data.startswith("admin_confirm_"))
async def admin_confirm_booking(callback: types.CallbackQuery):
    await callback.answer()
    booking_id = int(callback.data.split("_")[2])

    client_user_id = database.get_user_id_by_booking(booking_id)
    if client_user_id:
        # Уведомляем клиента
        await bot.send_message(
            chat_id=client_user_id,
            text="🟢 Ваша бронь подтверждена! Ожидайте звонка для уточнения места и времени встречи"
        )

    database.update_booking_status(booking_id, 'confirmed')
    await callback.message.edit_text("Заявка подтверждена")

@dp.callback_query(lambda c: c.data.startswith("admin_cancel_"))
async def admin_cancel_booking(callback: types.CallbackQuery):
    await callback.answer()
    booking_id = int(callback.data.split("_")[2])
    client_user_id = database.get_user_id_by_booking(booking_id)
    if client_user_id:
        # Уведомляем клиента
        await bot.send_message(
            chat_id=client_user_id,
            text="🔴 Ваша бронь отклонена"
        )
    database.update_booking_status(booking_id, 'cancelled')
    await callback.message.edit_text("Заявка отклонена")

@dp.callback_query(lambda c: c.data.startswith("admin_contact_"))
async def admin_contact_client(callback: types.CallbackQuery):
    await callback.answer()
    user_id = int(callback.data.split("_")[2])  # это тоже telegram_id
    
    client = database.get_client_by_tgid(user_id)
    
    if not client:
        await callback.message.answer("❌ Клиент не найден")
        return
    
    await callback.message.answer(
        f"👤 Клиент: {client['full_name']}\n"
        f"📞 Телефон: `{client['phone']}`\n\n",
        parse_mode='Markdown'
    )
#обработчик кнопки "Назад" в inline-клавиатуре
@dp.callback_query(lambda c: c.data == "admin_back_to_bookings")
async def admin_back_to_bookings(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    await callback.message.delete()
    
    if user_id not in admin_temp_data:
        await callback.message.answer("Ошибка. Начните заново с 'Все бронирования'")
        return
    
    status = admin_temp_data[user_id].get('status', 'pending')
    status_text = "ожидают подтверждения" if status == 'pending' else "ожидают встречи"
    
    bookings = database.get_all_bookings_with_details()
    filtered = [b for b in bookings if b['status'] == status]
    
    unique_clients = {}
    for b in filtered:
        client_id = b['client_id']
        if client_id not in unique_clients:
            unique_clients[client_id] = b['full_name']
    
    client_buttons = []
    for client_id, full_name in unique_clients.items():
        client_buttons.append([KeyboardButton(text=f"👤 {full_name}")])
    client_buttons.append([KeyboardButton(text="🔙 Назад")])
    
    # Убираем client_name, устанавливаем флаг что мы на уровне клиентов
    admin_temp_data[user_id].pop('client_name', None)
    admin_temp_data[user_id].pop('last_booking_id', None)
    admin_temp_data[user_id]['at_clients_level'] = True  # ← флаг
    
    client_keyboard = ReplyKeyboardMarkup(keyboard=client_buttons, resize_keyboard=True)
    await callback.message.answer(
        f"Клиенты, у которых есть брони со статусом '{status_text}':",
        reply_markup=client_keyboard
    )

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

#Мои бронирования (клиент)
@dp.message(lambda message: message.text == buttons.btn_show_my_bookings.text)
async def show_my_bookings(message: types.Message):
    user_id = message.from_user.id
    client = database.get_client_by_tgid(user_id)
    
    if not client:
        await message.answer("Сначала зарегистрируйтесь!")
        return
    
    bookings = database.get_client_bookings_with_details(client['client_id'])
    
    if not bookings:
        await message.answer("У вас пока нет бронирований.")
        return
    
    for booking in bookings:
        status_emoji = {
            'pending': '🟡',
            'confirmed': '🟢',
            'cancelled': '🔴'
        }.get(booking['status'], '⚪')
        
        status_text = {
            'pending': 'Ожидает подтверждения',
            'confirmed': 'Подтверждено',
            'cancelled': 'Отменено'
        }.get(booking['status'], 'Неизвестно')
        
        text = f"""
{status_emoji} *Бронирование #{booking['rental_id']}*

Машина: {booking['brand']} {booking['model']}
Даты: {booking['start_date']} — {booking['end_date']}
Стоимость: {booking['total_cost']}₽
Статус: {status_text}
"""
        if booking['status'] in ('pending', 'confirmed'):
            info_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Правила аренды", callback_data=f"rules_{booking['rental_id']}")],
                    [InlineKeyboardButton(text="Информация о встрече", callback_data=f"meeting_{booking['rental_id']}")]
                ]
            )
            await message.answer(text, parse_mode='Markdown', reply_markup=info_keyboard)
        else:
            await message.answer(text, parse_mode='Markdown')


#Правила аренды и инф о встрече
@dp.callback_query(lambda c: c.data.startswith("rules_"))
async def show_rules(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "Правила аренды\n\n"
        "Текст правил",
        parse_mode='Markdown'
    )

@dp.callback_query(lambda c: c.data.startswith("meeting_"))
async def show_meeting_info(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "Информация о встрече*\n\n"
        "*Текст о встрече",
        parse_mode='Markdown'
    )

@dp.message()
async def handle_all_messages(message: types.Message):
    user_id = message.from_user.id
    print(f"=== handle_all_messages: текст '{message.text}', user_id={user_id}")
    print(f"booking_step: {booking_step}")
    
    # Пропускаем админские кнопки с эмодзи
    if message.text and message.text.startswith(('👤', '🟡', '🟢', '🔙')):
        print("→ Админ-кнопка, пропускаем")
        return
    
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

