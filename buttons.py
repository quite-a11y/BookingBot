from aiogram.types import KeyboardButton,InlineKeyboardButton,InlineKeyboardMarkup
#Начальные кнопки
btn_start = KeyboardButton(text='Старт')
btn_help = KeyboardButton(text="Помощь")

#Кнопки после регистрации
btn_show_cars = KeyboardButton(text="Посмотреть все машины")
btn_show_my_bookings = KeyboardButton(text="Мои бронирования")
btn_reg = KeyboardButton(text="Зарегестрироваться")
btn_book_a_car = KeyboardButton(text='Забронировать машину')


#Инлайн кнопки при регистрациии и после регистрации
BACK_CALLBACK = 'back'
CANCEL_CALLBACK = "cancel"
CONFIRM_CALLBACK = "confirm"
btn_back = InlineKeyboardButton(text="Назад", callback_data=BACK_CALLBACK)
btn_cancel = InlineKeyboardButton(text="Отмена", callback_data=CANCEL_CALLBACK)
btn_confirm = InlineKeyboardButton(text="Подтвердить", callback_data=CONFIRM_CALLBACK)

#Инлайн кнопки при бронирование машин
FREE_CARS_CALLBACK = "free_cars"
BUSY_CARS_CALLBACK = "busy_cars"
btn_free = InlineKeyboardButton(text="Свободные машины", callback_data=FREE_CARS_CALLBACK)
btn_busy = InlineKeyboardButton(text="Занятые машины", callback_data=BUSY_CARS_CALLBACK)