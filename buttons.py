from aiogram.types import KeyboardButton,InlineKeyboardButton,InlineKeyboardMarkup
#Начальные кнопки
btn_start = KeyboardButton(text='Старт')
btn_help = KeyboardButton(text="Помощь")

#Кнопка админ панели
btn_admin_cars = KeyboardButton(text="Управление машинами")
btn_admin_all_cars = KeyboardButton(text='Все машины')
btn_admin_all_bookings = KeyboardButton(text="Все бронирования")
btn_add_car = KeyboardButton(text="Добавить машину")
btn_edit_car = KeyboardButton(text="Редактировать машину")
btn_delete_car = KeyboardButton(text="Удалить машину")
btn_back_to_admin = KeyboardButton(text="Назад")

#Кнопки после регистрации
btn_show_cars = KeyboardButton(text="Весь автопарк")
btn_show_my_bookings = KeyboardButton(text="Мои бронирования")
btn_reg = KeyboardButton(text="Зарегестрироваться")
btn_book_a_car = KeyboardButton(text='Забронировать машину')

#Инлайн кнопки загрзки фото сейчас/позже
btn_upload_now = InlineKeyboardButton(text='Загрузить сейчас', callback_data='upload_now')
btn_upload_later = InlineKeyboardButton(text='Загрузить позже', callback_data='upload_later')


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