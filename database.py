import sqlite3
from datetime import datetime
DB_NAME = 'valera_bot.db'
def get_connection():
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row #для возможности образения по именам колонки
    return connection

def init_db():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cars(
            car_id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER,
            price_per_day INTEGER,
            steering_wheel TEXT,
            transmission TEXT,
            color TEXT,
            engine_volume REAL,
            is_available INTEGER DEFAULT 1 
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients(
            client_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT UNIQUE,
            passport_series TEXT NOT NULL, 
            passport_number TEXT NOT NULL,
            passport_issued TEXT NOT NULL,
            date_of_issue TEXT NOT NULL,
            registration TEXT NOT NULL,
            telegram_id INTEGER NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings(
            rental_id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            total_cost INTEGER,
            status TEXT DEFAULT 'pending'
        )
    ''')
    try:
        cursor.execute('ALTER TABLE cars ADD COLUMN steering_wheel TEXT')
        cursor.execute('ALTER TABLE cars ADD COLUMN transmission TEXT')
        cursor.execute('ALTER TABLE cars ADD COLUMN color TEXT')
        cursor.execute('ALTER TABLE cars ADD COLUMN engine_volume REAL')
    except:
        pass

def add_client(full_name, phone, passport_series, passport_number, passport_issued, date_of_issue, registration, telegram_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('''
    INSERT INTO clients
    (full_name, phone, passport_series, passport_number, 
    passport_issued, date_of_issue, registration, telegram_id) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''
    ,(full_name, phone, passport_series, passport_number, passport_issued, date_of_issue, registration, telegram_id))
    connection.commit()
    client_id = cursor.lastrowid
    connection.close()
    return client_id

def get_client_by_phone(phone):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM clients WHERE phone = ?',(phone,))
    client_by_phone = cursor.fetchone()
    connection.close()
    return client_by_phone

def get_client_by_tgid(telegram_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM clients WHERE telegram_id = ?',(telegram_id,))
    client_by_tgid = cursor.fetchone()
    connection.close()
    return client_by_tgid

def get_all_cars():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM cars')
    cars = cursor.fetchall()
    connection.close()
    return cars

def get_avilable_cars(start_date,end_date):
    connection = get_connection()
    cursor = connection.cursor()
    st_date = datetime.strptime(start_date,'%d.%m.%Y %H:%M').strftime('%Y-%m-%d %H:%M')
    en_date = datetime.strptime(end_date,'%d.%m.%Y %H:%M').strftime('%Y-%m-%d %H:%M')
    cursor.execute('SELECT car_id FROM bookings WHERE start_date <= ? AND end_date >= ?',(en_date,st_date))
    list_not_avilable = cursor.fetchall()
    if list_not_avilable:
        not_avilable_cars_ids = [car[0] for car in list_not_avilable]
        placeholders = ','.join(['?'] * len(not_avilable_cars_ids))
        cursor.execute(f'''
            SELECT * FROM cars
            WHERE car_id NOT IN ({placeholders})
        ''',not_avilable_cars_ids)
    else:
        cursor.execute('SELECT * FROM cars')
    avilable_cars = cursor.fetchall()
    connection.close()
    return avilable_cars

def get_car_by_id(car_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM cars WHERE car_id = ?',(car_id,))
    car_by_id = cursor.fetchone()
    connection.close()
    return car_by_id

def get_car_full_info(car_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM cars WHERE car_id = ?', (car_id,))
    car = cursor.fetchone()
    connection.close()
    return car

def get_car_price(car_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT price_per_day FROM cars WHERE car_id = ?',(car_id,))
    car_price_by_id = cursor.fetchone()
    connection.close()
    return car_price_by_id[0] if car_price_by_id else None

def add_car(brand, model, year, price_per_day, steering_wheel, transmission, color, engine_volume):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('''
        INSERT INTO cars 
        (brand, model, year, price_per_day, steering_wheel, transmission, color, engine_volume) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (brand, model, year, price_per_day, steering_wheel, transmission, color, engine_volume))
    connection.commit()
    new_car_id = cursor.lastrowid
    connection.close()
    return new_car_id

def update_car_availability(car_id,is_available):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('UPDATE cars SET is_available = ? WHERE car_id = ?',(is_available,car_id))
    connection.commit()
    connection.close()
    if cursor.rowcount > 0:
        return True
    else:
        return False
    
def add_booking(car_id,client_id,start_date,end_date,total_cost,status='pending'):
    connection = get_connection()
    cursor = connection.cursor()
    st_date = datetime.strptime(start_date,'%d.%m.%Y %H:%M').strftime('%Y-%m-%d %H:%M')
    en_date = datetime.strptime(end_date,'%d.%m.%Y %H:%M').strftime('%Y-%m-%d %H:%M')
    cursor.execute('''INSERT INTO bookings 
                   (car_id,client_id,start_date,end_date,total_cost,status) 
                   VALUES (?, ?, ?, ?, ?, ?)''', 
                   (car_id,client_id,st_date,en_date,total_cost,status))
    connection.commit()
    new_booking_id = cursor.lastrowid
    connection.close()
    return new_booking_id
   
def get_bookings_by_client(client_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM bookings WHERE client_id = ? ORDER BY start_date DESC',(client_id,))
    history_of_bookings = cursor.fetchall()
    connection.close()
    return history_of_bookings
    
def get_all_bookings_admin():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('''
        SELECT 
            bookings.*,
            clients.full_name,
            clients.phone,
            cars.brand,
            cars.model
        FROM bookings
        JOIN clients ON bookings.client_id = clients.client_id
        JOIN cars ON bookings.car_id = cars.car_id
        ORDER BY bookings.start_date DESC
        ''')
    history_of_bookings_admin = cursor.fetchall()
    connection.close()
    return history_of_bookings_admin

def update_booking_status(booking_id, new_status):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('''
        UPDATE bookings SET status = ? WHERE rental_id = ? ''',
        (new_status,booking_id))
    connection.commit()
    updated_status = cursor.rowcount > 0 #true false
    connection.close()
    return updated_status

def get_bookings_by_date(cur_datetime):
    connection = get_connection()
    cursor = connection.cursor()
    current_date = datetime.strptime(cur_datetime,'%d.%m.%Y %H:%M').strftime('%Y-%m-%d %H:%M')
    cursor.execute('''
        SELECT 
            bookings.*,
            clients.full_name,
            clients.phone,
            cars.brand,
            cars.model
        FROM bookings
        JOIN clients ON bookings.client_id = clients.client_id
        JOIN cars ON bookings.car_id = cars.car_id
        WHERE start_date <= ? AND end_date >= ?
        ORDER BY bookings.start_date DESC
        ''',(current_date, current_date))
    current_data_booking = cursor.fetchall()
    connection.close()
    return current_data_booking

#def delete_old_bookings():
    
def get_booked_datetimes_for_car(car_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(''' 
        SELECT start_date, end_date 
        FROM bookings
        WHERE car_id = ?
    ''', (car_id,))
    booked_periods = cursor.fetchall()
    connection.close()
    return booked_periods


