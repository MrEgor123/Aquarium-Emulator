import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton,
                             QGraphicsPixmapItem, QGraphicsScene,
                             QGraphicsView, QFrame, QHBoxLayout, QWidget,
                             QVBoxLayout, QDialog)
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtGui import QPixmap, QFont, QTransform, QBrush, QColor, QPalette

# Константы для управления временем

# Таймер для уменьшения чистоты аквариума (в миллисекундах)
TIMER_CLEAN_AQUARIUM = 120000
# Таймер для уменьшения чистоты воды (в миллисекундах)
TIMER_CLEAN_WATER = 60000
# Таймер для обновления позиции рыбы (в миллисекундах)
TIMER_FISH_POSITION = 60000
# Таймер для обновления здоровья и голода рыбы (в миллисекундах)
TIMER_UPDATE_HEALTH = 16

# Константы для управления состоянием рыб и аквариума
FISH_HEALTH = 100  # Начальное здоровье рыбы
WATER_CLEAN = 100  # Начальная чистота воды
AQUARIUM_CLEAN = 100  # Начальная чистота аквариума
FISH_HUNGER = 100  # Максимальный уровень голода рыбы
FISH_BASE_HUNGER = 0  # Базовый уровень голода рыбы
FISH_SPEED = 1.2  # Скорость движения рыбы

# Константы для управления внешним видом кнопок
HEIGHT_BUTTON = 90  # Высота кнопок
SPACING_BUTTON = 20  # Расстояние между кнопками


def create_food_item(scene, pixmap, duration=5000, x=0, y=0):
    """Создает объект корма и добавляет его на сцену."""

    # Создаем объект QGraphicsPixmapItem для отображения корма
    food_item = QGraphicsPixmapItem(pixmap)
    # Устанавливаем начальную позицию корма
    food_item.setPos(x, y)

    # Добавляем объект корма на сцену
    scene.addItem(food_item)

    # Создаем таймер для анимации падения корма
    fall_timer = QTimer()

    def fall():
        """Функция, отвечающая за падение корма."""
        # Получаем текущую позицию корма
        current_pos = food_item.pos()
        # Вычисляем расстояние до дна
        distance = 899 - current_pos.y()
        # Вычисляем скорость падения,
        # чтобы корм упал за заданное время (duration)
        speed = distance / (duration / 50)
        # Вычисляем новую координату Y
        new_y = current_pos.y() + speed
        # Устанавливаем новую позицию корма
        food_item.setPos(current_pos.x(), new_y)

        # Если корм достиг дна, останавливаем таймер и удаляем корм со сцены
        if new_y >= 899:
            fall_timer.stop()
            scene.removeItem(food_item)

    # Подключаем функцию fall к таймеру, чтобы она вызывалась при каждом тике
    fall_timer.timeout.connect(fall)
    # Запускаем таймер с интервалом 50 миллисекунд
    fall_timer.start(50)


class MovingFish(QGraphicsPixmapItem):
    """Класс, представляющий движущуюся рыбу в аквариуме."""

    def __init__(self, x, y, scene_width, scene_height,
                 pixmap_path, fish_type, description, scale_factor=1):
        """Инициализирует объект MovingFish."""
        super().__init__()
        # Направление движения по оси X (1 - вправо, -1 - влево)
        self.direction_x = 1
        # Направление движения по оси Y (1 - вниз, -1 - вверх)
        self.direction_y = 1
        self.scene_width = scene_width  # Ширина сцены
        self.scene_height = scene_height  # Высота сцены
        # Оригинальное изображение рыбы
        self.original_pixmap = QPixmap(pixmap_path)
        # Флаг для отображения метки с информацией о рыбе
        self.label_visible = False
        # Тип рыбы
        self.fish_type = fish_type
        # Начальное здоровье рыбы
        self.health = FISH_HEALTH
        # Начальный уровень голода рыбы
        self.hunger = FISH_BASE_HUNGER
        # Описание рыбы
        self.description = description
        # Начальная чистота воды
        self.water_cleanliness = WATER_CLEAN
        # Начальная чистота аквариума
        self.aquarium_cleanliness = AQUARIUM_CLEAN

        # Загружаем и масштабируем изображение рыбы
        pixmap = QPixmap(pixmap_path)
        pixmap = pixmap.scaled(int(pixmap.width() * scale_factor),
                               int(pixmap.height() * scale_factor))
        self.setPixmap(pixmap)  # Устанавливаем изображение рыбы
        self.setPos(x, y)  # Устанавливаем начальную позицию
        # Разрешаем обработку событий наведения мыши
        self.setAcceptHoverEvents(True)

        # Создаем таймер для обновления состояния рыбы
        self.timer = QTimer()
        # Подключаем метод updateStatus к таймеру
        self.timer.timeout.connect(self.updateStatus)
        self.timer.start(TIMER_FISH_POSITION)  # Запускаем таймер

    def decreaseHealth(self):
        """Уменьшает здоровье рыбы на 2 единицы."""
        self.health -= 2
        self.health = max(0, self.health)  # Здоровье не может быть меньше 0

    def updateStatus(self):
        """Обновляет здоровье и голод рыбы."""
        self.decreaseHealth()  # Уменьшаем здоровье
        self.hunger += 1  # Увеличиваем голод
        # Голод не может быть больше максимального значения
        self.hunger = min(FISH_HUNGER, self.hunger)

    def getHungerLevel(self):
        """Возвращает уровень голода рыбы."""
        return self.hunger

    def feedFish(self):
        """Кормит рыбу, увеличивая ее здоровье и сбрасывая голод."""
        # Здоровье не может быть больше 100
        self.health = min(100, self.health + 100)
        self.hunger = 0  # Сбрасываем голод

    def mousePressEvent(self, event):
        """Обрабатывает событие нажатия мыши на рыбу."""
        super().mousePressEvent(event)
        window = self.scene().views()[0].window()  # Получаем главное окно
        window.showFishInfo(self)  # Показываем информацию о рыбе

    def updatePosition(self):
        """Обновляет позицию рыбы, двигая ее по сцене."""

        # Получаем текущую координату X
        current_x = self.x()

        # Получаем текущую координату Y
        current_y = self.y()

        # Вычисляем новую координату X, добавляя к текущей X координате
        # произведение направления по X на скорость рыбы
        new_x = current_x + self.direction_x * FISH_SPEED

        # Вычисляем новую координату Y, добавляя к текущей Y координате
        # произведение направления по Y на скорость рыбы
        new_y = current_y + self.direction_y * FISH_SPEED

        # Проверяем, не вышла ли рыба за левую
        # границу сцены (координата X меньше 0)
        if new_x < 0:
            # Если вышла, устанавливаем
            # координату X на границу (0)
            new_x = 0
            # Меняем направление движения по X на противоположное
            self.direction_x *= -1

        # Проверяем, не вышла ли рыба за правую границу сцены
        # (координата X больше ширины сцены минус ширина рыбы)
        elif new_x > self.scene_width - self.pixmap().width():
            # Если вышла, устанавливаем координату X на правую границу
            new_x = self.scene_width - self.pixmap().width()
            # Меняем направление движения по X на противоположное
            self.direction_x *= -1

        # Проверяем, не вышла ли рыба за
        # верхнюю границу сцены (координата Y меньше 0)
        if new_y < 0:
            # Если вышла, устанавливаем координату Y на границу (0)
            new_y = 0
            # Меняем направление движения по Y на противоположное
            self.direction_y *= -1

        # Проверяем, не вышла ли рыба за нижнюю границу сцены
        # (координата Y больше высоты сцены минус высота рыбы)
        elif new_y > self.scene_height - self.pixmap().height():
            # Если вышла, устанавливаем координату Y на нижнюю границу
            new_y = self.scene_height - self.pixmap().height()
            # Меняем направление движения по Y на противоположное
            self.direction_y *= -1

        # Устанавливаем новую позицию рыбы с учетом вычисленных координат
        self.setPos(new_x, new_y)

    def resetTransform(self):
        """Сбрасывает все преобразования изображения рыбы."""
        self.setTransform(QTransform())

    def paint(self, painter, option, widget):
        """Перерисовывает изображение рыбы."""
        painter.drawPixmap(
            0, 0, self.original_pixmap.scaled(
                self.pixmap().width(), self.pixmap().height()
            )
        )


class MyWindow(QMainWindow):
    """Основное окно приложения."""

    def __init__(self):
        """Инициализирует объект MyWindow."""
        super().__init__()
        self.water_item = None  # Элемент для отображения воды при ее смене
        self.food_items = []  # Список объектов корма
        # Путь к текущей директории
        self.current_directory = os.path.dirname(os.path.abspath(__file__))

        # Настройки окна
        self.setWindowTitle("Эмулятор Аквариума")  # Заголовок окна
        self.setFixedSize(1725, 950)  # Фиксированный размер окна

        # Создание сцены
        self.scene = QGraphicsScene(self)  # Создаем сцену
        self.scene.setSceneRect(0, 0, 1525, 700)  # Устанавливаем размер сцены

        # Создание вида
        self.view = QGraphicsView(self.scene, self)  # Создаем вид
        # Отключаем горизонтальную полосу прокрутки
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Отключаем вертикальную полосу прокрутки
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Устанавливаем режим обновления вида
        self.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        # Отключаем рамку вида
        self.view.setFrameShape(QFrame.NoFrame)
        # Выравниваем вид по левому верхнему углу
        self.view.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # Установка фона
        self.background_image_path = os.path.join(
            self.current_directory, "assets", "main.gif")
        # Загружаем фоновое изображение
        self.background_pixmap = QPixmap(self.background_image_path)
        # Создаем кисть с фоновым изображением
        background_brush = QBrush(self.background_pixmap)
        # Устанавливаем фон сцены
        self.scene.setBackgroundBrush(background_brush)

        # Добавление изображения для очистки воды
        self.clean_image_path = os.path.join(
            self.current_directory, "assets", "clean.gif")
        # Загружаем изображение
        clean_pixmap = QPixmap(self.clean_image_path)
        # Масштабируем изображение
        clean_pixmap = clean_pixmap.scaled(750, 750)
        # Создаем объект изображения
        self.clean_water_image_item = QGraphicsPixmapItem(clean_pixmap)
        # Устанавливаем позицию
        self.clean_water_image_item.setPos(350, 100)
        # Скрываем изображение
        self.clean_water_image_item.hide()
        # Добавляем изображение на сцену
        self.scene.addItem(self.clean_water_image_item)

        # Загрузка описаний рыб
        okun_description_path = os.path.join(
            self.current_directory, "assets", "Karas_description.txt")
        shuka_description_path = os.path.join(
            self.current_directory, "assets", "Shuka_description.txt")
        carp_description_path = os.path.join(
            self.current_directory, "assets", "Carp_description.txt")
        vobla_description_path = os.path.join(
            self.current_directory, "assets", "Vobla_description.txt")
        seld_description_path = os.path.join(
            self.current_directory, "assets", "Seld_description.txt")

        with open(okun_description_path, "r", encoding="utf-8") as file:
            Karas_description = file.read()  # Читаем описание карася
        with open(shuka_description_path, "r", encoding="utf-8") as file:
            Shuka_description = file.read()  # Читаем описание щуки
        with open(carp_description_path, "r", encoding="utf-8") as file:
            Carp_description = file.read()  # Читаем описание карпа
        with open(vobla_description_path, "r", encoding="utf-8") as file:
            Vobla_description = file.read()  # Читаем описание воблы
        with open(seld_description_path, "r", encoding="utf-8") as file:
            Seld_description = file.read()  # Читаем описание сельди

        # Создание рыб
        self.fishes = [
            MovingFish(
                200, 200, 1600, 900,
                os.path.join(self.current_directory, "assets", "fish1.gif"),
                "Карась",
                Karas_description),  # Создаем карася
            MovingFish(
                500, 300, 1600, 900,
                os.path.join(self.current_directory, "assets", "fish2.gif"),
                "Щука",
                Shuka_description),  # Создаем щуку
            MovingFish(
                700, 500, 1600, 900,
                os.path.join(self.current_directory, "assets", "fish3.gif"),
                "Карп",
                Carp_description),  # Создаем карпа
            MovingFish(
                1100, 50, 1600, 900,
                os.path.join(self.current_directory, "assets", "fish4.gif"),
                "Вобла",
                Vobla_description),  # Создаем воблу
            MovingFish(
                500, 50, 1600, 900,
                os.path.join(self.current_directory, "assets", "fish5.gif"),
                "Сельдь",
                Seld_description),  # Создаем сельдь
        ]

        # Добавление рыб на сцену
        for fish in self.fishes:
            self.scene.addItem(fish)  # Добавляем каждую рыбу на сцену

        # Создание кнопок
        self.setupButtons()  # Вызываем метод для создания кнопок

        # Создание меток
        self.current_label = None
        # Метка для отображения здоровья
        self.health_label = QLabel(self)
        # Устанавливаем размер и положение метки
        self.health_label.setGeometry(1300, 50, 200, 50)
        self.health_label.setStyleSheet(
            "color: white; font-weight: bold;")
        # Обновляем текст метки здоровья
        self.update_health_label()
        # Список меток для отображения голода каждой рыбы
        self.hunger_labels = []
        for i, fish in enumerate(self.fishes):
            # Создаем метку для отображения голода рыбы
            hunger_label = QLabel(self)
            # Устанавливаем размер и положение метки
            hunger_label.setGeometry(100, 250 + i * 100, 200, 50)
            hunger_label.setStyleSheet(
                "color: white; font-weight: bold;")
            # Добавляем метку в список
            self.hunger_labels.append(hunger_label)

        # Метка для отображения чистоты воды
        self.water_cleanliness_label = QLabel(self)
        # Устанавливаем размер и положение метки
        self.water_cleanliness_label.setGeometry(1300, 150, 200, 50)
        self.water_cleanliness_label.setStyleSheet(
            "color: white; font-weight: bold;")
        # Обновляем текст метки чистоты воды
        self.update_water_cleanliness_label()

        # Создание таймеров

        # Таймер для уменьшения чистоты аквариума
        self.cleanliness_timer = QTimer(self)
        # Подключаем метод decreaseCleanliness
        self.cleanliness_timer.timeout.connect(self.decreaseCleanliness)
        # Запускаем таймер
        self.cleanliness_timer.start(TIMER_CLEAN_AQUARIUM)

        # Таймер для уменьшения чистоты воды
        self.water_change_timer = QTimer(self)
        self.water_change_timer.timeout.connect(
            self.decreaseWaterCleanliness)
        # Запускаем таймер
        self.water_change_timer.start(TIMER_CLEAN_WATER)

        # Таймер для блокировки кнопки "Накормить рыб"
        self.feed_timer = QTimer(self)
        # Таймер сработает один раз
        self.feed_timer.setSingleShot(True)
        # Подключаем метод enableFeedButton
        self.feed_timer.timeout.connect(self.enableFeedButton)

        # Установка layout

        # Создаем центральный виджет
        central_widget = QWidget(self)
        # Устанавливаем центральный виджет
        self.setCentralWidget(central_widget)
        # Создаем главный layout
        main_layout = QVBoxLayout(central_widget)

        # Устанавливаем родителя для виджета с кнопками
        self.button_widget.setParent(central_widget)
        # Добавляем виджет с кнопками в главный layout
        main_layout.addWidget(self.button_widget)
        # Добавляем вид в главный layout
        main_layout.addWidget(self.view)

        # Показываем виджет с кнопками
        self.button_widget.show()

        # Установка градиентного фона
        palette = QPalette()  # Создаем палитру
        # Устанавливаем цвет фона
        palette.setColor(QPalette.Window, QColor(0, 123, 186))
        self.setPalette(palette)  # Применяем палитру

    def update_health_label(self):
        """Обновляет метку здоровья и запускает таймер для движения рыб."""
        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.moveFishes)
        self.move_timer.start(TIMER_UPDATE_HEALTH)

    def showFishInfo(self, fish):
        """Показывает диалоговое окно с информацией о выбранной рыбе."""
        dialog = QDialog(self)
        dialog.setWindowTitle(
            f"Информация о рыбе - {fish.fish_type.capitalize()}")
        fish_info = (
            f"<b>Тип рыбы:</b> {fish.fish_type.capitalize()}<br>"
            f"<b>Описание:</b> {fish.description}<br>"
            f"<b>Здоровье:</b> {fish.health}%<br>"
            f"<b>Голод:</b> {fish.hunger}%"
        )
        text_label = QLabel(fish_info)
        text_label.setFont(QFont(None, 14))
        text_label.setWordWrap(True)
        layout = QVBoxLayout()
        layout.addWidget(text_label)
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.close)
        layout.addWidget(ok_button)
        dialog.setLayout(layout)
        dialog.setFixedWidth(dialog.sizeHint().width())
        dialog.exec_()

    def moveFishes(self):
        """Запускает обновление позиции для каждой рыбы."""
        for fish in self.fishes:
            fish.updatePosition()

    def decreaseCleanliness(self):
        """Уменьшает уровень чистоты аквариума для каждой рыбы."""
        for fish in self.fishes:
            fish.aquarium_cleanliness -= 1
            fish.aquarium_cleanliness = max(0, fish.aquarium_cleanliness)
        self.update_water_cleanliness_label()

    def update_water_cleanliness_label(self):
        """Обновляет текстовое значение метки для чистоты воды."""
        return

    def decreaseWaterCleanliness(self):
        """Уменьшает уровень чистоты воды для каждой рыбы."""
        for fish in self.fishes:
            fish.water_cleanliness -= 1
            fish.water_cleanliness = max(0, fish.water_cleanliness)
        self.update_water_cleanliness_label()

    def feedFish(self):
        """Создает объекты еды и запускает их анимацию."""
        if not self.feed_timer.isActive():
            x_values = [200, 450, 700, 900, 1100]  # Координаты X для еды
            y_values = [1, 1, 1, 1, 1]  # Координаты Y для еды

            for x, y in zip(x_values, y_values):
                food_image_path = os.path.join(
                    self.current_directory, "assets", "food.gif")
                food_pixmap = QPixmap(food_image_path)
                create_food_item(self.scene,
                                 food_pixmap, duration=5000, x=x, y=y)

            # Обновляем состояние рыб после кормления
            for fish in self.fishes:
                fish.feedFish()
            self.update_health_label()
            self.update_status_label()
            QApplication.processEvents()

            # Блокируем кнопку на 5 секунд
            self.button2.setEnabled(False)
            self.feed_timer.start(5000)

    def enableFeedButton(self):
        """Разблокирует кнопку "Накормить рыб"."""
        self.button2.setEnabled(True)

    def update_status_label(self):
        """Обновляет текстовое значение метки для статуса."""
        return

    def setupButtons(self):
        """Создает кнопки и устанавливает их обработчики."""
        self.button1 = QPushButton("Правила", self)
        self.button2 = QPushButton("Накормить рыб", self)
        self.button3 = QPushButton("Почистить аквариум", self)
        self.rules_button = QPushButton("Поменять воду", self)
        self.state_button = QPushButton("Состояние аквариума", self)

        self.button1.clicked.connect(self.showRulesInfo)
        self.button2.clicked.connect(self.feedFish)
        self.button3.clicked.connect(self.clearAquarium)
        self.rules_button.clicked.connect(self.changeWater)
        self.state_button.clicked.connect(self.showAquariumState)

        # Создание layout для кнопок
        layout = QHBoxLayout()
        layout.addWidget(self.button1)
        layout.addWidget(self.button2)
        layout.addWidget(self.button3)
        layout.addWidget(self.rules_button)
        layout.addWidget(self.state_button)

        # Создание виджета для кнопок
        self.button_widget = QWidget(self)
        self.button_widget.setLayout(layout)

        # Установка стилей для кнопок
        button_height = HEIGHT_BUTTON
        button_spacing = SPACING_BUTTON
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(button_spacing)

        button_style = """
            QPushButton {
                background-color:
                qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                  stop: 0 #007bff,
                                                  stop: 1 #0056b3);
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color:
                qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                  stop: 0 #0069d9,
                                                  stop: 1 #004aa3);
            }
            QPushButton:pressed {
                background-color:
                qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                  stop: 0 #005cbf,
                                                  stop: 1 #00347a);
            }
        """
        self.button1.setStyleSheet(button_style)
        self.button2.setStyleSheet(button_style)
        self.button3.setStyleSheet(button_style)
        self.rules_button.setStyleSheet(button_style)
        self.state_button.setStyleSheet(button_style)

        # Установка высоты кнопок
        self.button1.setFixedHeight(button_height)
        self.button2.setFixedHeight(button_height)
        self.button3.setFixedHeight(button_height)
        self.rules_button.setFixedHeight(button_height)
        self.state_button.setFixedHeight(button_height)

        self.button_widget.installEventFilter(self)

    def showEatLabel(self):
        """Скрывает текущую метку."""
        self.hideCurrentLabel()
        self.current_label = None

    def clearAquarium(self):
        """Очищает аквариум, показывая анимацию и обновляя состояние."""
        self.clean_water_image_item.show()
        QTimer.singleShot(2000, self.hideCleanWater)

        for fish in self.fishes:
            fish.aquarium_cleanliness = AQUARIUM_CLEAN
        QApplication.processEvents()

    def hideCleanWater(self):
        """Скрывает изображение чистой воды."""
        self.clean_water_image_item.hide()

    def changeWater(self):
        """Меняет воду в аквариуме, показывая анимацию и обновляя состояние."""
        if self.water_item:
            self.scene.removeItem(self.water_item)

        water_image_path = os.path.join(
            self.current_directory, "assets", "water.gif")
        water_pixmap = QPixmap(water_image_path)
        water_item = QGraphicsPixmapItem(water_pixmap)
        water_item.setPos(0, 0)
        water_item.setZValue(-1)
        water_item.setTransformationMode(Qt.SmoothTransformation)
        water_item.setPixmap(water_pixmap.scaled(
            self.width(), self.height()))
        self.scene.addItem(water_item)
        self.water_item = water_item

        # Обновляем состояние рыб после смены воды
        for fish in self.fishes:
            fish.water_cleanliness = 100

        QTimer.singleShot(5000, lambda: self.scene.removeItem(water_item))

    def startWaterChange(self):
        """Запускает таймер для уменьшения чистоты воды."""
        self.update_water_cleanliness_label()
        self.water_change_timer = QTimer()
        self.water_change_timer.timeout.connect(
            self.decreaseWaterCleanliness)
        self.water_change_timer.start(TIMER_CLEAN_WATER)

    def showRulesInfo(self):
        """Показывает диалоговое окно с правилами игры."""
        current_directory = os.path.dirname(os.path.abspath(__file__))
        instructions_file_path = os.path.join(
            current_directory, "assets", "game_instructions.txt")
        with open(instructions_file_path, "r", encoding="utf-8") as file:
            game_instructions = file.read()

        dialog = QDialog(self)
        dialog.setWindowTitle("Правила")

        # Устанавливаем стиль шрифта для текста
        font = QFont(None, 14)

        # Устанавливаем текст с переносом строк
        text_label = QLabel(game_instructions.replace("\\n", "\n"))
        text_label.setFont(font)
        text_label.setWordWrap(True)
        layout = QVBoxLayout()
        layout.addWidget(text_label)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.close)
        layout.addWidget(ok_button)

        dialog.setLayout(layout)
        dialog.exec_()

    def showClearLabel(self):
        """Скрывает текущую метку."""
        self.hideCurrentLabel()
        self.current_label = None

    def showWaterLabel(self):
        """Скрывает текущую метку."""
        self.hideCurrentLabel()
        self.current_label = None

    def hideCurrentLabel(self):
        """Скрывает текущую метку, если она существует."""
        if self.current_label:
            self.current_label.hide()
            self.current_label.deleteLater()

    def resizeEvent(self, event):
        """Обрабатывает событие изменения размера окна, масштабируя фон."""
        super().resizeEvent(event)

        if self.scene.backgroundBrush().texture():
            scaled_pixmap = self.background_pixmap.scaled(
                self.width(), self.height(),
                Qt.KeepAspectRatioByExpanding
            )
            self.scene.setBackgroundBrush(QBrush(scaled_pixmap))

        # Обновляем положение виджета с кнопками
        self.button_widget.setGeometry(
            0, 0, self.width(), self.button_widget.height())

        self.updateFishBoundaries()

    def updateFishBoundaries(self):
        """Обновляет границы для движения рыб
        в соответствии с размером фона."""
        bg_rect = self.background_pixmap.rect()
        bg_scene_rect = self.view.mapToScene(bg_rect).boundingRect()
        for fish in self.fishes:
            fish.scene_width = bg_scene_rect.width()
            fish.scene_height = bg_scene_rect.height()

    def showAquariumState(self):
        """Показывает диалоговое окно с информацией о состоянии аквариума."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Состояние аквариума")

        layout = QVBoxLayout()

        # Вычисляем уровень чистоты воды
        total_water_cleanliness = sum(
            fish.water_cleanliness for fish in self.fishes) // len(
                self.fishes)

        # Создаем метку для уровня чистоты воды
        water_cleanliness_label = QLabel()
        water_cleanliness_label.setText(
            f"Уровень чистоты воды: {total_water_cleanliness}%")
        water_cleanliness_label.setFont(QFont(None, 14))
        layout.addWidget(water_cleanliness_label)

        # Вычисляем уровень чистоты аквариума
        total_cleanliness = sum(
            fish.aquarium_cleanliness for fish in self.fishes) // len(
                self.fishes)

        # Создаем метку для уровня чистоты аквариума
        cleanliness_label = QLabel(
            f"Уровень чистоты аквариума: {total_cleanliness}%")
        cleanliness_label.setFont(QFont(None, 14))
        layout.addWidget(cleanliness_label)

        ok_button = QPushButton("OK", dialog)
        ok_button.clicked.connect(dialog.close)
        layout.addWidget(ok_button)

        dialog.setLayout(layout)
        dialog.exec_()

    def eventFilter(self, obj, event):
        """Фильтрация событий для обработки нажатий на кнопки."""
        if (obj == self.button_widget
                and event.type() == QEvent.MouseButtonPress):
            mouse_pos = event.pos()
            for button in [self.button1, self.button2, self.button3,
                           self.rules_button, self.state_button]:
                if button.geometry().contains(mouse_pos):
                    button.click()
                    return True
        return super().eventFilter(obj, event)


def main():
    """Точка входа в приложение."""
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 12))
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
