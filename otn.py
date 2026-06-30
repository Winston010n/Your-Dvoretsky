import asyncio
import random
import os
from datetime import datetime

import aiohttp
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    Message, CallbackQuery
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ======================== ХРАНИЛИЩЕ В ПАМЯТИ ========================
users = {}
pairs = {}
wishes = {}
daily_bonuses = {}
anon_msgs = {}
msg_counter = 0

# ======================== ДАННЫЕ ДЛЯ ГЕНЕРАЦИИ ========================
DATE_IDEAS = [
    "Прогулка верхом 🐴", "Чтение баллад 🕯️", "Турнир ⚔️",
    "Пирог 🥧", "Герб 🛡️", "Пикник 🧺", "Фонарик 🏮", "Танцы 💃"
]
POEMS = [
    "В замке твоём я нашёл покой...",
    "Как роза в саду, ты прекрасна...",
    "Трубадур пою о любви..."
]
QUESTS = [
    ("Сделать комплимент", 15), ("Написать стих", 20),
    ("Приготовить завтрак", 25), ("Танцы под луной", 25),
    ("Подарить розу 🌹", 10), ("Совместное фото у памятника", 30)
]

COMPLIMENTS = {
    "knight": [
        "⚔️ Миледи, твоя красота затмевает звёзды.",
        "⚔️ Миледи, ты словно утренняя роса на лепестках роз.",
        "⚔️ Миледи, в твоих глазах отражаются звёзды.",
        "⚔️ Миледи, твой смех — музыка для моей души.",
        "⚔️ Миледи, ты прекрасна, как первый день весны.",
    ],
    "princess": [
        "👸 Мой рыцарь, твоя отвага вдохновляет меня.",
        "👸 Мой рыцарь, ты — мой защитник и герой.",
        "👸 Мой рыцарь, с тобой я в безопасности даже в бурю.",
        "👸 Мой рыцарь, ты — настоящий рыцарь без страха и упрёка.",
        "👸 Мой рыцарь, твои объятия — моё убежище.",
    ]
}

# ======================== МЕГА-КАТАЛОГ ПОДАРКОВ (360+ идей) ========================
GIFT_IDEAS = {
    "sport": {
        "free": [
            "Совместная пробежка в парке", "Утренняя зарядка под музыку",
            "Соревнование по отжиманиям", "Растяжка вдвоём",
            "Прыжки на скакалке на время", "Планка на рекорд",
            "Футбольный матч один на один", "Баскетбольный челлендж",
            "Катание на велосипедах", "Пеший поход по окрестностям"
        ],
        "budget": [
            "Абонемент в спортзал на месяц", "Фитнес-браслет",
            "Коврик для йоги", "Бутылка для воды с гравировкой",
            "Спортивный рюкзак", "Гантели",
            "Эспандер", "Скакалка с счётчиком",
            "Пояс для бега", "Спортивная футболка"
        ],
        "premium": [
            "Велосипед", "Умные часы для спорта",
            "Годовая карта в фитнес-клуб", "Экипировка для бега",
            "Домашний тренажёр", "Сноуборд",
            "Горные лыжи", "Абонемент в бассейн на год",
            "Персональный тренер на месяц", "Подарочный сертификат в спортивный магазин"
        ]
    },
    "creative": {
        "free": [
            "Рисунок вашей пары", "Песня, записанная на диктофон",
            "Стихотворение", "Самодельная открытка",
            "Коллаж из совместных фото", "Поделка из природных материалов",
            "Раскраска антистресс", "Написание совместной сказки",
            "Создание комикса про вас", "Оригами с признанием"
        ],
        "budget": [
            "Набор акварели", "Мастер-класс по гончарному делу",
            "Книга «Рисование для двоих»", "Билет на арт-выставку",
            "Мольберт настольный", "Альбом для скетчей",
            "Каллиграфический набор", "Краски по ткани",
            "Трафареты для декора", "Билет на керамический мастер-класс"
        ],
        "premium": [
            "Курс каллиграфии", "Профессиональный мольберт",
            "Портрет у художника", "Мастер-класс по масляной живописи",
            "Курс гончарного искусства", "3D-ручка",
            "Графический планшет", "Курс диджеинга",
            "Синтезатор", "Подарочный сертификат в художественный салон"
        ]
    },
    "romantic": {
        "free": [
            "Завтрак в постель", "Массаж при свечах",
            "Прогулка под луной", "Список 100 причин любви",
            "Звёздный пикник на крыше", "Совместное принятие ванны",
            "Просмотр фильма под пледами", "Создание капсулы времени",
            "Ужин при свечах дома", "Поэтический вечер"
        ],
        "budget": [
            "Ужин в ресторане", "Букет роз",
            "Парные кулоны", "Фотосессия",
            "Совместная спа-процедура", "Билеты в кино на последний ряд",
            "Сертификат на романтический ужин", "Парные браслеты",
            "Коробка с предсказаниями", "Свеча с ароматом любви"
        ],
        "premium": [
            "Полёт на воздушном шаре", "Романтическое путешествие",
            "Ювелирное украшение", "Ночь в замке",
            "Ужин на крыше небоскрёба", "Спа-выходные",
            "Парные часы", "Поездка на лимузине",
            "Сертификат на фотосессию в средневековых костюмах",
            "Золотой кулон с инициалами"
        ]
    },
    "adventure": {
        "free": [
            "Квест по городу", "Геокешинг",
            "Поход в лес", "Фотоохота на закате",
            "Спуск с горы на велосипедах", "Прыжки в воду с пирса",
            "Покорение заброшенного здания", "Скалолазание на естественном рельефе",
            "Ночная прогулка с фонариками", "Паркур-тренировка"
        ],
        "budget": [
            "Билеты на квеструм", "Катание на лошадях",
            "Прыжок с моста (тарзанка)", "Дайвинг-сессия",
            "Аренда квадроциклов", "Полёт на параплане (тариф эконом)",
            "Каякинг", "Сплавы на байдарках",
            "Экскурсия на джипах", "Билеты на веревочный парк"
        ],
        "premium": [
            "Полёт на параплане", "Сафари на джипах",
            "Скайдайвинг", "Путешествие на воздушном шаре",
            "Дайвинг с аквалангом", "Рафтинг по горной реке",
            "Альпинистское восхождение", "Кругосветное путешествие",
            "Сертификат на прыжок с парашютом", "Экспедиция в дикую природу"
        ]
    },
    "foodie": {
        "free": [
            "Домашняя пицца", "Совместная готовка ужина",
            "Дегустация сыров дома", "Печенье с предсказаниями",
            "Приготовление коктейлей", "Вечер фондю",
            "Мастер-класс по приготовлению суши дома", "Барбекю во дворе",
            "Создание своего рецепта", "Украшение торта"
        ],
        "budget": [
            "Мастер-класс по суши", "Подписка на доставку кофе",
            "Корзина деликатесов", "Ужин в темноте",
            "Набор для приготовления коктейлей", "Книга рецептов",
            "Форма для выпечки", "Сертификат в кулинарную студию",
            "Сет специй", "Билет на гастрофестиваль"
        ],
        "premium": [
            "Ужин от шеф-повара на дому", "Винный тур",
            "Ресторан со звёздами Мишлен", "Гастро-выходные",
            "Курс бариста", "Мастер-класс по молекулярной кухне",
            "Подарочный сертификат в ресторан", "Абонемент на дегустации",
            "Шоколадный фондан ручной работы", "Ужин на яхте"
        ]
    },
    "geek": {
        "free": [
            "Марафон фильмов по вселенной", "Настолки дома",
            "Совместное прохождение игры", "Викторина по интересам",
            "Создание гиковского квеста", "Обсуждение комиксов",
            "Косплей дома", "Сборка пазла на 1000 деталей",
            "Просмотр аниме", "Написание фанфика"
        ],
        "budget": [
            "Новая настольная игра", "Футболка с принтом",
            "Комикс", "Стикеры на ноутбук",
            "Чехол для телефона с героем", "Постер любимого фильма",
            "Кружка-хамелеон", "Набор для покраски миниатюр",
            "Билет на гик-фестиваль", "Подписка на стриминговый сервис"
        ],
        "premium": [
            "Коллекционное издание игры", "VR-шлем",
            "Билет на Comic Con", "Сборка ПК",
            "Ретро-консоль", "Фигурка ограниченного тиража",
            "Световой меч", "Косплей-костюм на заказ",
            "Годовая подписка на World of Warcraft", "Коллекционная карта"
        ]
    },
    "music": {
        "free": [
            "Плейлист на Spotify", "Домашний караоке",
            "Запись кавера", "Танец под любимую песню",
            "Совместное музицирование", "Прослушивание винила",
            "Создание музыкального клипа", "Поход на уличный концерт",
            "Изучение нового инструмента", "Вечер воспоминаний с саундтреками"
        ],
        "budget": [
            "Билеты на концерт", "Виниловая пластинка",
            "Портативная колонка", "Наушники",
            "Укулеле", "Губная гармошка",
            "Нотная тетрадь", "Сертификат в музыкальный магазин",
            "Билет на музыкальный фестиваль", "Подписка на музыкальный сервис"
        ],
        "premium": [
            "Инструмент (гитара, синтезатор)", "Абонемент на фестиваль",
            "Профессиональный микрофон", "Домашняя студия звукозаписи",
            "Билеты в VIP-ложу", "Колонки Hi-Fi",
            "Курс вокала", "Электрогитара с усилителем",
            "Наушники студийного качества", "Коллекционная пластинка"
        ]
    },
    "fashion": {
        "free": [
            "Стилизация старой одежды", "Совместный шопинг-челлендж",
            "Обмен гардеробами на вечер", "Модный показ дома",
            "Переделка футболок", "Создание аксессуаров",
            "Макияж-вечеринка", "Примерка образов из Pinterest",
            "Фотосессия в новых луках", "Ревизия гардероба"
        ],
        "budget": [
            "Дизайнерская футболка", "Кожаный ремень",
            "Шарф ручной работы", "Парные носки",
            "Стильная кепка", "Кошелёк",
            "Сумка-шопер", "Бижутерия",
            "Сертификат в магазин одежды", "Ремешок для часов"
        ],
        "premium": [
            "Брендовая сумка", "Костюм на заказ",
            "Ювелирное украшение", "Дизайнерские очки",
            "Кожаная куртка", "Эксклюзивные кроссовки",
            "Подарочный сертификат в бутик", "Персонализированный халат",
            "Золотые запонки", "Кашемировый свитер"
        ]
    },
    "travel": {
        "free": [
            "Виртуальная экскурсия", "План будущего путешествия",
            "Просмотр тревел-шоу", "Изучение языка страны мечты",
            "Составление карты желаний", "Вечер воспоминаний о поездках",
            "Пикник в стиле другой страны", "Создание travel-блога",
            "Обмен валютой разных стран", "Онлайн-тур по музею"
        ],
        "budget": [
            "Поездка в соседний город", "Билеты на автобус до озера",
            "Палатка для кемпинга", "Путеводитель",
            "Чемодан", "Органайзер для багажа",
            "Дорожная подушка", "Сертификат на экскурсию",
            "Карта мира на стену", "Скретч-карта"
        ],
        "premium": [
            "Путёвка на море", "Авиабилеты в Европу",
            "Круиз", "Горнолыжный тур",
            "Сафари в Африке", "Путешествие на поезде класса люкс",
            "Аренда яхты", "Годовой абонемент в аэропортные лаунджи",
            "Индивидуальный гид", "Фотоальбом ручной работы"
        ]
    },
    "books": {
        "free": [
            "Обмен любимыми книгами", "Совместное чтение вслух",
            "Создание своей сказки", "Посещение библиотеки",
            "Литературный вечер", "Написание рецензии",
            "Буккроссинг", "Чтение стихов",
            "Создание закладок", "Книжный клуб вдвоём"
        ],
        "budget": [
            "Подарочное издание", "Электронная книга",
            "Подписка на библиотеку", "Книжный бокс",
            "Светильник для чтения", "Подставка для книг",
            "Закладка с гравировкой", "Сертификат в книжный магазин",
            "Блокнот для заметок", "Магнитные закладки"
        ],
        "premium": [
            "Коллекционное издание", "Книжный шкаф",
            "Курс писательского мастерства", "Встреча с автором",
            "Антикварная книга", "Библиотека мировой классики",
            "Электронная книга с подсветкой", "Подписка на аудиокниги",
            "Именной экслибрис", "Книга в кожаном переплёте"
        ]
    },
    "tech": {
        "free": [
            "Чистка ноутбука", "Установка полезного софта",
            "Создание общего облака", "Настройка умного дома",
            "Обновление прошивки", "Организация кабелей",
            "Чистка клавиатуры", "Оптимизация системы",
            "Резервное копирование данных", "Настройка VPN"
        ],
        "budget": [
            "Беспроводная зарядка", "Селфи-палка",
            "USB-хаб", "Чехол для телефона",
            "Защитное стекло", "Внешний аккумулятор",
            "Флешка", "Карта памяти",
            "Подставка для ноутбука", "USB-лампа"
        ],
        "premium": [
            "Смартфон", "Планшет",
            "Умные часы", "Ноутбук",
            "Игровая консоль", "Монитор",
            "Клавиатура механическая", "Мышь игровая",
            "SSD-накопитель", "Экшн-камера"
        ]
    },
    "health": {
        "free": [
            "Сеанс медитации", "Утренняя йога",
            "Детокс-день вдвоём", "Дыхательные упражнения",
            "Травяной чай", "Контрастный душ",
            "Массаж стоп", "Здоровый завтрак",
            "Прогулка босиком", "Солевая ванна"
        ],
        "budget": [
            "Массажёр", "Аромадиффузор",
            "Фитнес-трекер", "Ортопедическая подушка",
            "Коврик для йоги", "Эспандер",
            "Бутылка для воды с разметкой", "Сертификат на массаж",
            "Набор эфирных масел", "Грелка"
        ],
        "premium": [
            "Массажное кресло", "Солярий",
            "Курс массажа", "Фитнес-трекер премиум",
            "Абонемент в спа", "Ортопедический матрас",
            "Стайлер для волос", "Ирригатор",
            "Электрическая зубная щётка", "Билет в термальный комплекс"
        ]
    }
}

DREAM_PARTS = {
    "morning": ["🌅 Встретить рассвет с какао", "🥐 Завтрак в пекарне", "🧘 Совместная йога"],
    "afternoon": ["🚲 Поездка на велосипедах", "🎨 Мастер-класс по рисованию", "🏰 Посещение замка"],
    "evening": ["🍝 Ужин при свечах", "🎬 Кино под открытым небом", "💃 Танцы на закате"],
    "night": ["⭐ Звёзды с телескопом", "🔥 Костер и маршмеллоу", "🛁 Ванна с лепестками роз"]
}

# ======================== ФУНКЦИИ ========================
def get_user(uid: int) -> dict:
    if uid not in users:
        users[uid] = {
            "role": None, "exp": 0, "level": 1, "title": "",
            "pair_id": None, "achievements": [], "married": False
        }
    return users[uid]

def add_exp(uid: int, amount: int):
    u = get_user(uid)
    u["exp"] += amount
    u["level"] = u["exp"] // 100 + 1
    r = u.get("role")
    if r:
        titles = {
            "knight": {1: "Оруженосец", 2: "Рыцарь", 3: "Барон", 4: "Граф", 5: "Герцог", 6: "Король"},
            "princess": {1: "Фрейлина", 2: "Баронесса", 3: "Графиня", 4: "Герцогиня", 5: "Королева", 6: "Императрица"}
        }
        u["title"] = titles[r].get(min(u["level"], 6), titles[r][6])

def add_achievement(uid: int, ach: str):
    u = get_user(uid)
    if ach not in u["achievements"]:
        u["achievements"].append(ach)

def get_partner(uid: int) -> int | None:
    return pairs.get(uid)

def is_group(event) -> bool:
    if isinstance(event, Message):
        return event.chat.type in ["group", "supergroup"]
    elif isinstance(event, CallbackQuery):
        return event.message.chat.type in ["group", "supergroup"] if event.message else False
    return False

def generate_love_letter(role: str, style: str) -> str:
    if role == "knight":
        if style == "passion":
            return "О моя пламенная королева!\n\nТы — ураган, сметающий всё на пути. Твои глаза — огонь, губы — сладкий яд. Я готов сгореть в этом пламени.\n\nЯ буду твоим щитом и мечом.\n\nТвой навеки, пылающий рыцарь."
        elif style == "gentle":
            return "Моя нежная лилия\n\nТихий шелест твоих шагов слаще музыки. Твоя улыбка — рассвет после ночи. Я хочу держать тебя за руку и молчать.\n\nОбещаю быть твоей опорой.\n\nВечно твой, преданный рыцарь."
        else:
            return "Моя драконоукротительница\n\nТы украла мой покой, мои мысли, и даже последний кусок пиццы — и я счастлив!\n\nКлянусь делить с тобой всё, включая Wi-Fi пароль.\n\nТвой немного сумасшедший рыцарь."
    else:
        if style == "passion":
            return "Мой неукротимый рыцарь\n\nТвоя сила притягивает как магнит. Когда ты рядом, сердце бьётся в ритме боевых барабанов.\n\nС тобой я готова на любые подвиги.\n\nТвоя страстная леди."
        elif style == "gentle":
            return "Мой ласковый воин\n\nТы — моя тихая гавань. В твоих объятиях я забываю обо всём.\n\nЯ буду ждать тебя у окна.\n\nС нежностью, твоя принцесса."
        else:
            return "Мой чемпион по поеданию пиццы\n\nТы единственный, кто понимает мой сарказм. С тобой даже проигрывать весело.\n\nОбещаю не ворчать (ну, почти).\n\nТвоя неидеальная, но счастливая леди."

# ======================== КЛАВИАТУРЫ ========================
MAIN_PRIVATE = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎲 Выбор", callback_data="choose"),
     InlineKeyboardButton(text="💡 Идея", callback_data="idea")],
    [InlineKeyboardButton(text="👤 Профиль", callback_data="prof"),
     InlineKeyboardButton(text="💑 Пары", callback_data="pair_menu")],
    [InlineKeyboardButton(text="🎁 Подарки", callback_data="gift_menu"),
     InlineKeyboardButton(text="💭 Идеи подарков", callback_data="gift_ideas_menu")],
    [InlineKeyboardButton(text="📍 Места", callback_data="loc"),
     InlineKeyboardButton(text="📅 Свидание мечты", callback_data="dream")],
    [InlineKeyboardButton(text="📜 Письмо", callback_data="love"),
     InlineKeyboardButton(text="💌 Комплимент", callback_data="comp")],
    [InlineKeyboardButton(text="🎁 Бонус", callback_data="bonus"),
     InlineKeyboardButton(text="🎰 Сюрприз", callback_data="surp")],
    [InlineKeyboardButton(text="👸 Хотелки", callback_data="wish_menu"),
     InlineKeyboardButton(text="📬 Советник", callback_data="anon")],
    [InlineKeyboardButton(text="📖 Справка", callback_data="help")]
])

MAIN_GROUP = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎲 Выбор", callback_data="choose"),
     InlineKeyboardButton(text="💡 Идея", callback_data="idea")],
    [InlineKeyboardButton(text="💑 Пары", callback_data="pair_menu"),
     InlineKeyboardButton(text="📍 Места", callback_data="loc")],
    [InlineKeyboardButton(text="📜 Письмо", callback_data="love"),
     InlineKeyboardButton(text="💌 Комплимент", callback_data="comp")],
    [InlineKeyboardButton(text="📖 Помощь", callback_data="help")]
])

ROLE_KB = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⚔️ Рыцарь", callback_data="role_k"),
     InlineKeyboardButton(text="👸 Принцесса", callback_data="role_p")]
])

# ======================== FSM ========================
class PairJoin(StatesGroup):
    code = State()

class ChoiceState(StatesGroup):
    opts = State()

class AnonMsg(StatesGroup):
    text = State()

class WishAdd(StatesGroup):
    w = State()

# ======================== ОБРАБОТЧИКИ ========================
@dp.message(Command("start"))
async def start(msg: Message):
    if is_group(msg):
        await msg.answer("🏰 Дворецкий в чате! Используйте /help")
    else:
        await msg.answer("🏰 Добро пожаловать! Выберите роль:", reply_markup=ROLE_KB)

@dp.message(Command("help"))
async def help_cmd(msg: Message):
    await help_info(msg)

@dp.callback_query(F.data == "help")
async def help_cb(cb: CallbackQuery):
    await help_info(cb)

async def help_info(event):
    text = (
        "📖 Справка\n\n"
        "🎲 Выбор — варианты через запятую\n"
        "💡 Идея свидания\n"
        "👤 Профиль (только в ЛС)\n"
        "💑 Пары — создать или присоединиться\n"
        "🎁 Подарки — отправить партнёру\n"
        "💭 Идеи подарков — 360+ вариантов по интересам\n"
        "📍 Места — отправьте геопозицию\n"
        "📅 Свидание мечты — план на день\n"
        "📜 Письмо — в трёх стилях\n"
        "💌 Комплимент — приятные слова\n"
        "🎁 Ежедневный бонус\n"
        "🎰 Сюрприз — случайная идея подарка\n"
        "👸 Хотелки — сохранить желания\n"
        "📬 Советник — анонимное сообщение создателю\n\n"
        "Команды: /quest, /poem, /wedding, /help"
    )
    kb = MAIN_PRIVATE if not is_group(event) else MAIN_GROUP
    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb)
    else:
        await event.message.edit_text(text, reply_markup=kb)
        await event.answer()

@dp.callback_query(F.data.startswith("role_"))
async def set_role(cb: CallbackQuery):
    if is_group(cb):
        await cb.answer("Выбор роли только в ЛС. Напишите мне в личку.", show_alert=True)
        return
    role = "knight" if cb.data == "role_k" else "princess"
    get_user(cb.from_user.id)["role"] = role
    add_exp(cb.from_user.id, 0)
    greeting = "⚔️ Доблестный рыцарь, ваш замок ждёт!" if role == "knight" else "👸 Прекрасная леди, добро пожаловать!"
    await cb.message.edit_text(greeting, reply_markup=MAIN_PRIVATE)
    await cb.answer()

@dp.callback_query(F.data == "prof")
async def prof(cb: CallbackQuery):
    if is_group(cb):
        await cb.answer("Профиль только в ЛС.", show_alert=True)
        return
    u = get_user(cb.from_user.id)
    if not u.get("role"):
        await cb.message.edit_text("Сначала выберите роль через /start")
        return
    p = get_partner(cb.from_user.id)
    pinfo = "Нет пары"
    if p:
        pu = get_user(p)
        pinfo = f"{pu.get('title','')} ({'⚔️' if pu.get('role')=='knight' else '👸'})"
    text = (
        f"📜 Профиль\n"
        f"🎭 Роль: {'⚔️ Рыцарь' if u['role']=='knight' else '👸 Принцесса'}\n"
        f"🏅 Титул: {u['title']}\n"
        f"✨ Уровень: {u['level']} (опыт: {u['exp']})\n"
        f"💑 Пара: {pinfo}\n"
        f"💍 Брак: {'Да' if u.get('married') else 'Нет'}\n"
        f"🏆 Достижения: {', '.join(u['achievements']) if u['achievements'] else 'пока нет'}"
    )
    await cb.message.edit_text(text, reply_markup=MAIN_PRIVATE)
    await cb.answer()

@dp.callback_query(F.data == "pair_menu")
async def pair_menu(cb: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать", callback_data="p_create"),
         InlineKeyboardButton(text="🔗 Присоединиться", callback_data="p_join")]
    ])
    await cb.message.edit_text("💑 Управление парой:", reply_markup=kb)
    await cb.answer()

@dp.callback_query(F.data == "p_create")
async def p_create(cb: CallbackQuery):
    uid = cb.from_user.id
    code = str(random.randint(10000, 99999))
    get_user(uid)["pair_id"] = code
    pairs[uid] = None
    add_exp(uid, 10)
    await cb.message.edit_text(f"✅ Пара создана! Код: <code>{code}</code>\nПередайте его партнёру.")
    await cb.answer()

@dp.callback_query(F.data == "p_join")
async def p_join(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("Введите код пары:")
    await state.set_state(PairJoin.code)
    await cb.answer()

@dp.message(PairJoin.code)
async def p_join_code(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    code = msg.text.strip()
    partner = None
    for other_uid, other in users.items():
        if other.get("pair_id") == code and other_uid != uid:
            partner = other_uid
            break
    if not partner:
        await msg.answer("❌ Неверный код или пара уже полна.")
        await state.clear()
        return
    get_user(uid)["pair_id"] = code
    get_user(partner)["pair_id"] = code
    pairs[uid] = partner
    pairs[partner] = uid
    add_exp(uid, 15)
    add_exp(partner, 10)
    await msg.answer("💑 Вы в паре! Теперь вы связаны узами.")
    try:
        await bot.send_message(partner, "💑 Ваш партнёр присоединился! Теперь вы вместе.")
    except:
        pass
    await state.clear()

@dp.callback_query(F.data == "choose")
async def choose(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("Отправьте варианты через запятую:")
    await state.set_state(ChoiceState.opts)
    await cb.answer()

@dp.message(ChoiceState.opts)
async def choose_do(msg: Message, state: FSMContext):
    opts = [x.strip() for x in msg.text.split(",") if x.strip()]
    if len(opts) < 2:
        await msg.answer("Минимум два варианта.")
        return
    u = get_user(msg.from_user.id)
    role = u.get("role", "knight")
    chosen = max(opts, key=len) if role == "knight" else min(opts, key=len)
    add_exp(msg.from_user.id, 5)
    await msg.answer(f"{'⚔️' if role=='knight' else '👸'} [{u.get('title','')}] Ваш выбор: <b>{chosen}</b>")
    await state.clear()

@dp.callback_query(F.data == "idea")
async def idea(cb: CallbackQuery):
    add_exp(cb.from_user.id, 2)
    idea = random.choice(DATE_IDEAS)
    await cb.message.edit_text(
        f"💡 Идея для свидания: <b>{idea}</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Другая", callback_data="idea"),
             InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
        ])
    )
    await cb.answer()

@dp.callback_query(F.data == "loc")
async def loc_prompt(cb: CallbackQuery):
    await cb.message.edit_text("📍 Отправьте вашу геопозицию (через скрепку).")
    await cb.answer()

@dp.message(F.location)
async def handle_location(msg: Message):
    lat, lon = msg.location.latitude, msg.location.longitude
    add_exp(msg.from_user.id, 3)
    wait = await msg.answer("🔎 Ищу места для свиданий...")

    weather = "🌤 Погода недоступна."
    if OPENWEATHER_API_KEY:
        try:
            async with aiohttp.ClientSession() as s:
                url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
                async with s.get(url, timeout=aiohttp.ClientTimeout(total=3)) as resp:
                    data = await resp.json()
                    weather = f"🌡 {data.get('name','?')}: {data['weather'][0]['description']}, {data['main']['temp']}°C"
        except:
            pass

    places = []
    try:
        async with aiohttp.ClientSession() as s:
            query = f"[out:json];(node[amenity~'cafe|restaurant|bar'](around:2000,{lat},{lon});node[leisure=park](around:2000,{lat},{lon}););out 8;"
            async with s.post("https://overpass-api.de/api/interpreter", data=query, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                places = [el.get("tags", {}).get("name", "?") for el in data["elements"] if "name" in el.get("tags", {})]
    except:
        pass

    if places:
        result = f"{weather}\n\n📍 Места рядом:\n" + "\n".join(f"• {p}" for p in places[:6])
    else:
        result = f"{weather}\n\n😔 Рядом не найдено интересных мест."
    await wait.edit_text(result)

@dp.callback_query(F.data == "comp")
async def comp(cb: CallbackQuery):
    u = get_user(cb.from_user.id)
    role = u.get("role", "knight")
    text = random.choice(COMPLIMENTS.get(role, COMPLIMENTS["knight"]))
    add_exp(cb.from_user.id, 3)
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Ещё", callback_data="comp"),
         InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ]))
    await cb.answer()

@dp.callback_query(F.data == "love")
async def love(cb: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Страсть", callback_data="ls_pass"),
         InlineKeyboardButton(text="🌸 Нежность", callback_data="ls_gentle"),
         InlineKeyboardButton(text="😂 Юмор", callback_data="ls_humor")]
    ])
    await cb.message.edit_text("Выберите стиль письма:", reply_markup=kb)
    await cb.answer()

@dp.callback_query(F.data.startswith("ls_"))
async def love_style(cb: CallbackQuery):
    style = cb.data.split("_")[1]
    u = get_user(cb.from_user.id)
    role = u.get("role", "knight")
    letter = generate_love_letter(role, style)
    add_exp(cb.from_user.id, 7)
    await cb.message.edit_text(
        f"📜 Любовное письмо:\n\n{letter}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Другое", callback_data="love"),
             InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
        ])
    )
    await cb.answer()

@dp.callback_query(F.data == "dream")
async def dream(cb: CallbackQuery):
    plan = (
        f"📅 Свидание мечты\n\n"
        f"☀️ Утро: {random.choice(DREAM_PARTS['morning'])}\n"
        f"🌤 День: {random.choice(DREAM_PARTS['afternoon'])}\n"
        f"🌆 Вечер: {random.choice(DREAM_PARTS['evening'])}\n"
        f"🌙 Ночь: {random.choice(DREAM_PARTS['night'])}"
    )
    add_exp(cb.from_user.id, 5)
    await cb.message.edit_text(plan, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Другой план", callback_data="dream"),
         InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ]))
    await cb.answer()

@dp.callback_query(F.data == "bonus")
async def bonus(cb: CallbackQuery):
    if is_group(cb):
        await cb.answer("Бонус только в ЛС.", show_alert=True)
        return
    uid = cb.from_user.id
    today = datetime.now().strftime("%Y-%m-%d")
    if daily_bonuses.get(uid) == today:
        await cb.message.edit_text("🎁 Вы уже получили сегодняшний бонус. Завтра приходите снова!", reply_markup=MAIN_PRIVATE)
        await cb.answer()
        return
    daily_bonuses[uid] = today
    if random.random() < 0.5:
        amount = random.randint(10, 25)
        add_exp(uid, amount)
        text = f"⚡ Вы получили {amount} опыта!"
    else:
        u = get_user(uid)
        text = random.choice(COMPLIMENTS.get(u.get("role", "knight"), COMPLIMENTS["knight"]))
    add_achievement(uid, "Ежедневный дар")
    await cb.message.edit_text(f"🎁 Ежедневный бонус:\n{text}", reply_markup=MAIN_PRIVATE)
    await cb.answer()

@dp.callback_query(F.data == "surp")
async def surp(cb: CallbackQuery):
    interest = random.choice(list(GIFT_IDEAS.keys()))
    budget = random.choice(["free", "budget", "premium"])
    idea = random.choice(GIFT_IDEAS[interest][budget])
    add_exp(cb.from_user.id, 3)
    await cb.message.edit_text(
        f"🎁 Сюрприз-подарок:\n\n{idea}\n_(Категория: {interest}, бюджет: {budget})_",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎰 Ещё сюрприз", callback_data="surp"),
             InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
        ])
    )
    await cb.answer()

@dp.callback_query(F.data == "gift_menu")
async def gift_menu(cb: CallbackQuery):
    partner = get_partner(cb.from_user.id)
    if not partner:
        await cb.message.edit_text("💔 Чтобы дарить подарки, нужна пара. Создайте её в разделе 💑 Пары.")
        await cb.answer()
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌹 Роза", callback_data="gift_rose"),
         InlineKeyboardButton(text="💍 Кольцо", callback_data="gift_ring")],
        [InlineKeyboardButton(text="👑 Корона", callback_data="gift_crown"),
         InlineKeyboardButton(text="❤️ Сердце", callback_data="gift_heart")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])
    await cb.message.edit_text("🎁 Выберите подарок для вашей второй половинки:", reply_markup=kb)
    await cb.answer()

@dp.callback_query(F.data.startswith("gift_"))
async def gift_send(cb: CallbackQuery):
    partner = get_partner(cb.from_user.id)
    if not partner:
        await cb.message.edit_text("Нет пары.")
        await cb.answer()
        return
    gift = cb.data.split("_")[1]
    gifts_dict = {"rose": "🌹 Роза", "ring": "💍 Кольцо", "crown": "👑 Корона", "heart": "❤️ Сердце"}
    await cb.message.edit_text(f"✅ Вы подарили {gifts_dict[gift]}!")
    try:
        await bot.send_message(partner, f"🎁 Ваш партнёр дарит вам {gifts_dict[gift]}!")
    except:
        pass
    add_exp(cb.from_user.id, 20)
    add_achievement(cb.from_user.id, "Даритель")
    await cb.answer()

@dp.callback_query(F.data == "gift_ideas_menu")
async def gift_ideas_menu(cb: CallbackQuery):
    builder = InlineKeyboardBuilder()
    interests = {
        "sport": "⚽ Спорт", "creative": "🎨 Творчество", "romantic": "💕 Романтика",
        "adventure": "🌍 Приключения", "foodie": "🍕 Гурман", "geek": "🎮 Гик",
        "music": "🎵 Музыка", "fashion": "👗 Мода", "travel": "✈️ Путешествия",
        "books": "📚 Книги", "tech": "💻 Техника", "health": "🧘 Здоровье"
    }
    for k, v in interests.items():
        builder.add(InlineKeyboardButton(text=v, callback_data=f"gi_{k}"))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🎲 Случайный интерес", callback_data="gi_random"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
    await cb.message.edit_text("💭 Выберите увлечение партнёра (360+ идей!):", reply_markup=builder.as_markup())
    await cb.answer()

@dp.callback_query(F.data.startswith("gi_"))
async def gi(cb: CallbackQuery):
    interest = cb.data.split("_")[1]
    if interest == "random":
        interest = random.choice(list(GIFT_IDEAS.keys()))
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="💝 Бесплатные", callback_data=f"gb_{interest}_free"))
    builder.add(InlineKeyboardButton(text="💰 Бюджетные", callback_data=f"gb_{interest}_budget"))
    builder.add(InlineKeyboardButton(text="👑 Премиум", callback_data=f"gb_{interest}_premium"))
    builder.add(InlineKeyboardButton(text="🎲 Случайный бюджет", callback_data=f"gb_{interest}_random"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="gift_ideas_menu"))
    await cb.message.edit_text(f"Выбрано: {interest}\nТеперь выберите бюджет:", reply_markup=builder.as_markup())
    await cb.answer()

@dp.callback_query(F.data.startswith("gb_"))
async def gb(cb: CallbackQuery):
    _, interest, budget = cb.data.split("_")
    if budget == "random":
        budget = random.choice(["free", "budget", "premium"])
    ideas = GIFT_IDEAS.get(interest, {}).get(budget, ["Нет идей"])
    text = f"💭 Идеи подарков ({interest}, {budget}):\n\n" + "\n".join(f"{i+1}. {x}" for i, x in enumerate(ideas))
    add_exp(cb.from_user.id, 5)
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Другие идеи", callback_data=f"gb_{interest}_{budget}"),
         InlineKeyboardButton(text="💼 Другой интерес", callback_data="gift_ideas_menu")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ]))
    await cb.answer()

@dp.callback_query(F.data == "wish_menu")
async def wish_menu(cb: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить желание", callback_data="w_add"),
         InlineKeyboardButton(text="📋 Мои желания", callback_data="w_my")],
        [InlineKeyboardButton(text="💑 Желания пары", callback_data="w_pair"),
         InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])
    await cb.message.edit_text("👸 Хотелки:", reply_markup=kb)
    await cb.answer()

@dp.callback_query(F.data == "w_add")
async def w_add(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("Отправьте текст, фото или голосовое — я сохраню как желание.")
    await state.set_state(WishAdd.w)
    await cb.answer()

@dp.message(WishAdd.w)
async def w_save(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    if uid not in wishes:
        wishes[uid] = []
    content = msg.text or msg.caption or "Медиа-желание"
    wishes[uid].append({"text": content, "time": datetime.now().strftime("%d.%m %H:%M")})
    add_exp(uid, 5)
    add_achievement(uid, "Хотелка")
    await msg.answer("✅ Желание сохранено в вашем списке!")
    await state.clear()

@dp.callback_query(F.data == "w_my")
async def w_my(cb: CallbackQuery):
    uid = cb.from_user.id
    wlist = wishes.get(uid, [])
    if not wlist:
        await cb.message.edit_text("У вас пока нет сохранённых желаний.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="wish_menu")]
        ]))
    else:
        text = "📋 Ваши желания:\n\n" + "\n".join(f"• {w['text']} ({w['time']})" for w in wlist[-10:])
        await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="wish_menu")]
        ]))
    await cb.answer()

@dp.callback_query(F.data == "w_pair")
async def w_pair(cb: CallbackQuery):
    uid = cb.from_user.id
    partner = get_partner(uid)
    if not partner:
        await cb.message.edit_text("У вас нет пары.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="wish_menu")]
        ]))
        await cb.answer()
        return
    wlist = wishes.get(partner, [])
    if not wlist:
        await cb.message.edit_text("У партнёра пока нет желаний.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="wish_menu")]
        ]))
    else:
        text = "💑 Желания партнёра:\n\n" + "\n".join(f"• {w['text']} ({w['time']})" for w in wlist[-10:])
        await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="wish_menu")]
        ]))
    await cb.answer()

@dp.callback_query(F.data == "anon")
async def anon(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("📬 Напишите ваше сообщение, идею или вопрос. Оно будет доставлено анонимно.")
    await state.set_state(AnonMsg.text)
    await cb.answer()

@dp.message(AnonMsg.text)
async def anon_send(msg: Message, state: FSMContext):
    global msg_counter
    msg_counter += 1
    anon_msgs[msg_counter] = {"uid": msg.from_user.id, "text": msg.text}
    if ADMIN_ID:
        try:
            await bot.send_message(ADMIN_ID, f"📬 Анонимное сообщение #{msg_counter}\nОт: {msg.from_user.id}\n\n{msg.text}\n\nОтветьте: /reply {msg_counter} <ваш ответ>")
        except:
            pass
    await msg.answer("✅ Ваше сообщение отправлено советнику. Ответ придёт в этот же чат.")
    await state.clear()

@dp.message(Command("reply"))
async def reply(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    parts = msg.text.split(maxsplit=2)
    if len(parts) < 3:
        await msg.answer("/reply <id> <текст>")
        return
    try:
        mid = int(parts[1])
    except:
        await msg.answer("Неверный ID.")
        return
    if mid not in anon_msgs:
        await msg.answer("Сообщение не найдено.")
        return
    uid = anon_msgs[mid]["uid"]
    try:
        await bot.send_message(uid, f"📬 Ответ советника:\n\n{parts[2]}")
        await msg.answer("✅ Ответ отправлен.")
    except:
        await msg.answer("Не удалось отправить ответ пользователю.")

@dp.message(Command("quest"))
async def quest(msg: Message):
    q, exp = random.choice(QUESTS)
    add_exp(msg.from_user.id, exp)
    add_achievement(msg.from_user.id, "Квест")
    await msg.answer(f"📜 Ежедневный квест: {q}\nНаграда: +{exp} опыта")

@dp.message(Command("poem"))
async def poem(msg: Message):
    add_exp(msg.from_user.id, 5)
    await msg.answer(f"🎭 Стихотворение:\n\n{random.choice(POEMS)}")

@dp.message(Command("wedding"))
async def wedding(msg: Message):
    u = get_user(msg.from_user.id)
    if u.get("married"):
        await msg.answer("💍 Вы уже состоите в браке!")
        return
    if u.get("level", 0) < 6:
        await msg.answer("Для брака нужен 6 уровень (Король/Королева). Выполняйте квесты!")
        return
    p = get_partner(msg.from_user.id)
    if not p:
        await msg.answer("У вас нет пары. Брак невозможен.")
        return
    u["married"] = True
    get_user(p)["married"] = True
    add_achievement(msg.from_user.id, "Свадьба")
    add_achievement(p, "Свадьба")
    await msg.answer("💒 Поздравляю! Вы сочетались узами брака в нашем замке! 🎉")
    try:
        await bot.send_message(p, "💍 Ваш партнёр предложил вечный союз! Вы теперь муж и жена в глазах королевства.")
    except:
        pass

@dp.callback_query(F.data == "back")
async def back(cb: CallbackQuery):
    if is_group(cb):
        await cb.message.edit_text("🏰 Главный зал:", reply_markup=MAIN_GROUP)
    else:
        await cb.message.edit_text("🏰 Главный зал:", reply_markup=MAIN_PRIVATE)
    await cb.answer()

async def main():
    print("🏰 Средневековый дворецкий Lightning запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())