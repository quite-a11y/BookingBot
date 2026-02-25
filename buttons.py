from aiogram.types import KeyboardButton,InlineKeyboardButton,InlineKeyboardMarkup
#Начальные кнопки
btn_show_cars = KeyboardButton(text="Посмотреть все машины")
btn_show_my_bookings = KeyboardButton(text="Мои бронирования")
btn_help = KeyboardButton(text="Помощь")
btn_reg = KeyboardButton(text="Зарегестрироваться")
btn_start = KeyboardButton(text='Старт')



BACK_CALLBACK = 'back'
CANCEL_CALLBACK = "cancel"
CONFIRM_CALLBACK = "confirm"
EDIT_CALLBACK = "edit"

btn_back = InlineKeyboardButton(text="Назад", callback_data=BACK_CALLBACK)
btn_cancel = InlineKeyboardButton(text="Отмена", callback_data=CANCEL_CALLBACK)
btn_confirm = InlineKeyboardButton(text="Подтвердить", callback_data=CONFIRM_CALLBACK)
btn_edit = InlineKeyboardButton(text="Изменить", callback_data=EDIT_CALLBACK)


