import asyncio
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import requests
import sqlite3
from cfg import TOKEN


class FSMAdmin(StatesGroup):
    artikuladd = State()
    artikuldel = State()


storage = MemoryStorage()

con = sqlite3.connect("users")
cur = con.cursor()


bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)
headers = {
    "User-Agent":
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    'Accept': '*/*'}
i1 = types.KeyboardButton('Посмотреть все отслеживаемые товары на Wildberries')
i2 = types.KeyboardButton('Поставить товар с Wildberries на слежку за ценой')
i3 = types.KeyboardButton('Остановить слежку за товаром на Wildberries')
main_rkb = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_rkb.add(i1).add(i2).add(i3)


@dp.message_handler(commands='start')
async def start(message: types.Message):
    await bot.send_message(message.chat.id, 'Привет, я - телеграмм бот для отслеживания цен товаров.',
                           reply_markup=main_rkb)
    if (message.chat.id,) not in cur.execute('SELECT user_id FROM first').fetchall():
        loop = asyncio.get_event_loop()
        loop.create_task(all_prices_check(message.chat.id))


@dp.message_handler(content_types='text', state=None)
async def text_understend(message: types.Message):
    # WILDBERRIES

    if message.text == 'Поставить товар с Wildberries на слежку за ценой':
        rkb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        rkb.add('Стоп')
        await FSMAdmin.artikuladd.set()
        await bot.send_message(message.chat.id, 'Введите артикул товара или нажмите "Стоп" для остановки',
                               reply_markup=rkb)
    elif message.text == 'Остановить слежку за товаром на Wildberries':
        if (message.chat.id,) in cur.execute('SELECT user_id FROM first').fetchall():
            rkb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            rkb.add('Стоп', 'Удалить всё')
            await FSMAdmin.artikuldel.set()
            await bot.send_message(message.chat.id, 'Введите артикул товара, за которым хотите остановить слежку',
                                   reply_markup=rkb)
        else:
            await bot.send_message(message.chat.id, 'Вы не следите ни за одним товаром')
    elif message.text == 'Посмотреть все отслеживаемые товары на Wildberries':
        if (message.chat.id,) in cur.execute('SELECT user_id FROM first').fetchall():
            for i in cur.execute('SELECT goods_id, name, price, image FROM first WHERE user_id = ?',
                                 (message.chat.id,)).fetchall():
                await bot.send_photo(message.chat.id, i[3],
                                     caption=f'Артикул: {i[0]}\nНазвание: {i[1]}\nНынешняя цена: {i[2]}')
                await asyncio.sleep(0.5)
        else:
            await bot.send_message(message.chat.id, 'У вас нет отслеживаемых товаров')


@dp.message_handler(content_types='text', state=FSMAdmin.artikuladd)
async def price_get(message: types.Message, state: FSMContext):
    if message.text == 'Стоп':
        await bot.send_message(message.chat.id, 'Бот перестал принимать артикулы', reply_markup=main_rkb)
        await state.finish()
    elif (message.text,) not in \
            cur.execute('SELECT goods_id FROM first WHERE user_id = ?', (message.chat.id,)).fetchall():
        r = requests.get(
            f'https://card.wb.ru/cards/detail?appType=1&curr=rub&dest='
            f'-1257786&regions=80,38,4,64,83,33,68,70,69,30,86,75,40,1,66,110,22,31,48,71,114&spp=0&nm={message.text}',
            headers=headers)
        if len(r.json().get('data').get('products')) != 0:
            names = r.json().get('data').get('products')[0].get('name')
            price = r.json().get('data').get('products')[0].get('salePriceU') / 100
            idd = message.text
            for i in range(1, 13):
                if i < 10:
                    if requests.get(
                            f'https://basket-0{i}.wb.ru/vol{idd[:len(idd) - 5]}'
                            f'/part{idd[:len(idd) - 3]}/{idd}/images/c246x328/1.jpg',
                            headers=headers).status_code == 200:
                        picture = f'https://basket-0{i}.wb.ru/vol' \
                                  f'{idd[:len(idd) - 5]}/part{idd[:len(idd) - 3]}/{idd}/images/c246x328/1.jpg'
                        await bot.send_photo(message.chat.id,
                                             photo=f'https://basket-0{i}.wb.ru/vol'
                                                   f'{idd[:len(idd) - 5]}/part'
                                                   f'{idd[:len(idd) - 3]}/{idd}/images/c246x328/1.jpg',
                                             caption=f'Товар {names} найден.'
                                                     f'\nМожете ввести еще один артикул товара или нажать на кнопку '
                                                     f'"Стоп" чтобы бот перестал принимать артикулы')
                        break
                else:
                    if requests.get(
                            f'https://basket-{i}.wb.ru/vol{idd[:len(idd) - 5]}'
                            f'/part{idd[:len(idd) - 3]}/{idd}/images/c246x328/1.jpg',
                            headers=headers).status_code == 200:
                        picture = f'https://basket-{i}.wb.ru/vol{idd[:len(idd) - 5]}' \
                                  f'/part{idd[:len(idd) - 3]}/{idd}/images/c246x328/1.jpg'
                        await bot.send_photo(message.chat.id,
                                             photo=f'https://basket-{i}.wb.ru/vol{idd[:len(idd) - 5]}'
                                                   f'/part{idd[:len(idd) - 3]}/{idd}/images/c246x328/1.jpg',
                                             caption=f'Товар {names} найден.'
                                                     f'\nМожете ввести еще один артикул товара или нажать на кнопку '
                                                     f'"Стоп" чтобы бот перестал принимать артикулы')
                        break
            cur.execute('INSERT INTO first(user_id, goods_id, name, price, image) VALUES(?, ?, ?, ?, ?)',
                        (message.chat.id, idd, names, price, picture))
            con.commit()
        else:
            await message.answer(
                f'Товар с артикулом {message.text} не найден. Введите еще один артикул или нажмите на кнопку "Стоп"')
    else:
        await bot.send_message(message.chat.id, 'Данный товар уже отслеживается')


@dp.message_handler(content_types='text', state=FSMAdmin.artikuldel)
async def art_del(message: types.Message, state: FSMContext):
    if message.text == 'Стоп':
        await state.finish()
        await bot.send_message(message.chat.id, 'Бот перестал принимать артикулы', reply_markup=main_rkb)
    elif message.text == 'Удалить всё':
        cur.execute('DELETE FROM first WHERE user_id = ?', (message.chat.id,))
        con.commit()
        await state.finish()
        await bot.send_message(message.chat.id, 'Все товары удалены', reply_markup=main_rkb)
    else:
        if (message.text,) in cur.execute('SELECT goods_id FROM first WHERE user_id = ?',
                                          (message.chat.id,)).fetchall():
            await bot.send_photo(message.chat.id,
                                 caption=
                                 f'Товар {cur.execute("SELECT name FROM first WHERE goods_id = ? and user_id = ?", (str(message.text), message.chat.id)).fetchone()[0]} больше не отслеживается. Введите еще один артикул, нажмите "Стоп" или "Удалить всё"',
                                 photo=cur.execute("SELECT image FROM first WHERE goods_id = ? and user_id = ?",
                                                   (str(message.text), message.chat.id)).fetchone()[0])
            cur.execute('DELETE FROM first WHERE goods_id = ? and user_id = ?', (message.text, message.chat.id))
            con.commit()
        else:
            await bot.send_message(message.chat.id,
                                   'Данный товар не отслеживался ранее. '
                                   'Введите еще один артикул, нажмите "Стоп" или "Удалить всё"')


async def all_prices_check(us_id):
    while True:
        for i in cur.execute('SELECT goods_id, name, price, image FROM first WHERE user_id = ?', (us_id,)):
            r = requests.get(
                f'https://card.wb.ru/cards/detail?appType=1&curr=rub&dest='
                f'-1257786&regions=80,38,4,64,83,33,68,70,69,30,86,75,40,1,66,110,22,31,48,71,114&spp=0&nm={i[0]}',
                headers=headers)
            price = r.json().get('data').get('products')[0].get('salePriceU') / 100
            if i[2] < price:
                await bot.send_photo(us_id, photo=i[3], caption=f'⬆Цена товара {i[1]} выросла с {i[2]} до {price}')
                cur.execute('DELETE FROM first WHERE goods_id = ? and user_id = ?', (i[0], us_id))
                con.commit()
                cur.execute('INSERT INTO first(user_id, goods_id, name, price, image) VALUES(?, ?, ?, ?, ?)',
                            (us_id, i[0], i[1], price, i[3]))
                con.commit()
            elif i[2] > price:
                await bot.send_photo(us_id, photo=i[3], caption=f'⬇Цена товара {i[1]} уменьшилась с {i[2]} до {price}')
                cur.execute('DELETE FROM first WHERE goods_id = ? and user_id = ?', (i[0], us_id))
                con.commit()
                cur.execute('INSERT INTO first(user_id, goods_id, name, price, image) VALUES(?, ?, ?, ?, ?)',
                            (us_id, i[0], i[1], price, i[3]))
                con.commit()
        await asyncio.sleep(21600)


for us in cur.execute('SELECT user_id FROM first').fetchall():
    loop = asyncio.get_event_loop()
    loop.create_task(all_prices_check(us[0]))

if __name__ == '__main__':
    executor.start_polling(dp)
# 21600
