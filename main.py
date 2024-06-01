import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton,
                             QGraphicsPixmapItem, QGraphicsScene,
                             QGraphicsView, QFrame, QHBoxLayout, QWidget,
                             QVBoxLayout, QDialog)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QTransform, QBrush
import os

TIMER_CLEAN_AQUARIUM = 120000  # Изменено! Изначально: 120000
TIMER_CLEAN_WATER = 60000  # Изменено! Изначально: 60000
TIMER_FISH_POSITION = 60000  # Изменено! Изначально: 60000
TIMER_UPDATE_HEALTH = 16
FISH_HEALTH = 100
WATER_CLEAN = 100
AQUARIUM_CLEAN = 100
FISH_HUNGER = 100
FISH_BASE_HUNGER = 0
FISH_SPEED = 1.2
HEIGHT_BUTTON = 90
SPACING_BUTTON = 20


class FoodItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, duration=5000, x=0, y=0, parent=None):
        super().__init__(pixmap, parent)
        self.duration = duration
        self.setPos(x, y)  # Установка начальной позиции корма

        # Создаем таймер для перемещения корма вниз
        self.fall_timer = QTimer()
        self.fall_timer.timeout.connect(self.fall)
        self.fall_timer.start(50)  # Падение обновляется каждые 50 миллисекунд

    def fall(self):
        current_pos = self.pos()
        # Расстояние до нижней границы сцены
        distance = 899 - current_pos.y()
        # Скорость опускания в пикселях за миллисекунду
        speed = distance / (self.duration / 50)
        # Новая позиция по оси Y
        new_y = current_pos.y() + speed
        self.setPos(current_pos.x(), new_y)
        # Если достигли нижней границы сцены
        if new_y >= 899:
            # Останавливаем таймер
            self.fall_timer.stop()
            # Удаляем корм
            self.scene().removeItem(self)


class MovingFish(QGraphicsPixmapItem):
    musicClicked = pyqtSignal()

    def __init__(self, x, y, scene_width, scene_height,
                 pixmap_path, fish_type, description, scale_factor=1):
        super().__init__()
        self.direction_x = 1
        self.direction_y = 1
        self.scene_width = scene_width
        self.scene_height = scene_height
        self.original_pixmap = QPixmap(pixmap_path)
        self.scene_width = scene_width
        self.scene_height = scene_height
        self.label_visible = False
        self.fish_type = fish_type
        self.health = FISH_HEALTH  # Изначальное здоровье рыбы
        self.hunger = FISH_BASE_HUNGER  # Изначальный уровень голода рыбы
        self.description = description  # Описание рыбы
        self.water_cleanliness = WATER_CLEAN  # Чистота ваоды в аквариуме
        self.aquarium_cleanliness = AQUARIUM_CLEAN  # Чистота аквариума

        pixmap = QPixmap(pixmap_path)
        pixmap = pixmap.scaled(int(pixmap.width() * scale_factor),
                               int(pixmap.height() * scale_factor))
        self.setPixmap(pixmap)
        self.setPos(x, y)
        # Включаем обработку событий мыши для рыбы
        self.setAcceptHoverEvents(True)

        # Создаем таймер для уменьшения здоровья
        # и увеличения голода рыбы каждую минуту
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateStatus)

        # Таймер срабатывает каждую минуту (60000 миллисекунд)
        self.timer.start(TIMER_FISH_POSITION)

    def decreaseHealth(self):
        self.health -= 2
        if self.health < 0:
            self.health = 0
        # Обновление метки на интерфейсе, после изменения здоровья
        if self.scene() and self.scene().views():
            window = self.scene().views()[0].window()
            window.update_health_label()

    def updateStatus(self):
        self.decreaseHealth()

        self.hunger += 1
        if self.hunger > FISH_HUNGER:
            self.hunger = FISH_HUNGER

        # Обновление метки на интерфейсе, после изменения голода и здоровья
        if self.scene() and self.scene().views():
            window = self.scene().views()[0].window()
            window.update_status_label()

    def getHungerLevel(self):  # Голод рыб
        return self.hunger

    def feedFish(self):
        self.health = min(100, self.health + 100)  # Увеличение здоровья рыбы
        self.hunger = 0  # Сбрасывание уровня голода

        if self.fish_type == "carp":
            print(self.description)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        window = self.scene().views()[0].window()
        window.showFishInfo(self)
        self.direction = 1

    def updatePosition(self):
        current_x = self.x()
        current_y = self.y()

        # Скорость движения по горизонтали
        new_x = current_x + self.direction_x * FISH_SPEED
        # Скорость движения по вертикали
        new_y = current_y + self.direction_y * FISH_SPEED
        # Проверка новых координат в пределах окна
        if 0 <= new_x <= self.scene_width - self.pixmap().width():
            self.setX(new_x)
        else:
            # Если рыба достигла края по горизонтали,
            # меняем направление по горизонтали
            self.direction_x *= -1
        if 0 <= new_y <= self.scene_height - self.pixmap().height():
            self.setY(new_y)
        else:
            # Если рыба достигла края по вертикали,
            # меняем направление по вертикали
            self.direction_y *= -1

        # Обновление координат рыбы, относительно верхнего левого угла
        self.setPos(self.mapToParent(0, 0))

    def resetTransform(self):
        self.setTransform(QTransform())  # Сброс всех преобразований

    def paint(self, painter, option, widget):
        # Перерисовать изображение с учетом измененного масштаба и поворота
        painter.drawPixmap(
            0, 0, self.original_pixmap.scaled(
                self.pixmap().width(), self.pixmap().height()
                )
            )


class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.water_item = None
        self.food_items = []
        self.current_directory = os.path.dirname(os.path.abspath(__file__))
        self.clean_image_path = os.path.join(
            self.current_directory, "assets", "clean.gif")
        clean_pixmap = QPixmap(self.clean_image_path)
        # Изменяем размеры изображения
        clean_pixmap = clean_pixmap.scaled(750, 750)
        self.clean_water_image_item = QGraphicsPixmapItem(clean_pixmap)
        # Устанавливаем положение изображения на сцене
        self.clean_water_image_item.setPos(350, 100)
        self.clean_water_image_item.hide()
        self.scene = QGraphicsScene(self)
        self.scene.addItem(self.clean_water_image_item)

        okun_description_path = os.path.join(
            self.current_directory, "assets", "Okun_description.txt")
        shuka_description_path = os.path.join(
            self.current_directory, "assets", "Shuka_description.txt")
        carp_description_path = os.path.join(
            self.current_directory, "assets", "Carp_description.txt")
        vobla_description_path = os.path.join(
            self.current_directory, "assets", "Vobla_description.txt")
        seld_description_path = os.path.join(
            self.current_directory, "assets", "Seld_description.txt")

        self.setWindowTitle("Эмулятор Аквариума")
        self.setFixedSize(1525, 950)
        self.scene.setSceneRect(0, 0, 1525, 899)  # Set scene size

        self.view = QGraphicsView(self.scene, self)
        self.setCentralWidget(self.view)

        self.background_image_path = os.path.join(
            self.current_directory, "assets", "main.gif")
        background_pixmap = QPixmap(self.background_image_path)
        background_brush = QBrush(background_pixmap)
        self.scene.setBackgroundBrush(background_brush)

        self.view.setScene(self.scene)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.view.setFrameShape(QFrame.NoFrame)
        # Фиксируем сцену в верхнем левом углу
        self.view.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        # Приводим размеры сцены к целым числам
        self.view.setFixedSize(
            int(self.scene.width()), int(self.scene.height()))

        with open(okun_description_path, "r") as file:
            Okun_description = file.read()
        with open(shuka_description_path, "r") as file:
            Shuka_description = file.read()
        with open(carp_description_path, "r") as file:
            Carp_description = file.read()
        with open(vobla_description_path, "r") as file:
            Vobla_description = file.read()
        with open(seld_description_path, "r") as file:
            Seld_description = file.read()

        self.fishes = [
            MovingFish(
                200, 200, 1600, 900,
                os.path.join(self.current_directory, "assets", "fish1.gif"),
                "Окунь",
                Okun_description),
            MovingFish(
                500, 300, 1600, 900,
                os.path.join(self.current_directory, "assets", "fish2.gif"),
                "Щука",
                Shuka_description),
            MovingFish(
                700, 500, 1600, 900,
                os.path.join(self.current_directory, "assets", "fish3.gif"),
                "Карп",
                Carp_description),
            MovingFish(
                1100, 50, 1600, 900,
                os.path.join(self.current_directory, "assets", "fish4.gif"),
                "Вобла",
                Vobla_description),
            MovingFish(
                500, 50, 1600, 900,
                os.path.join(self.current_directory, "assets", "fish5.gif"),
                "Сельдь",
                Seld_description),
        ]

        for fish in self.fishes:
            self.scene.addItem(fish)
        self.setupButtons()
        self.current_label = None
        self.resizeEvent(None)
        self.health_label = QLabel(self)
        self.health_label.setGeometry(1300, 50, 200, 50)
        self.health_label.setStyleSheet("color: black;")
        self.update_health_label()
        self.hunger_labels = []

        for i, fish in enumerate(self.fishes):
            hunger_label = QLabel(self)
            hunger_label.setGeometry(100, 250 + i * 100, 200, 50)
            hunger_label.setStyleSheet("color: black;")
            self.hunger_labels.append(hunger_label)

        self.water_cleanliness_label = QLabel(self)
        self.water_cleanliness_label.setGeometry(1300, 150, 200, 50)
        self.water_cleanliness_label.setStyleSheet("color: black;")
        self.update_water_cleanliness_label()

        self.cleanliness_timer = QTimer(self)
        self.cleanliness_timer.timeout.connect(self.decreaseCleanliness)
        # Таймер срабатывает каждые две минуты (120000 миллисекунд)
        self.cleanliness_timer.start(TIMER_CLEAN_AQUARIUM)

        self.water_change_timer = QTimer(self)
        self.water_change_timer.timeout.connect(self.decreaseWaterCleanliness)
        # Таймер срабатывает каждую минуту (60000 миллисекунд)
        self.water_change_timer.start(TIMER_CLEAN_WATER)

    def update_health_label(self):
        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.moveFishes)
        self.move_timer.start(TIMER_UPDATE_HEALTH)

    def showFishInfo(self, fish):
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
        text_label.setWordWrap(True)  # Включаем автоматический перенос слов

        layout = QVBoxLayout()
        layout.addWidget(text_label)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.close)
        layout.addWidget(ok_button)

        dialog.setLayout(layout)
        dialog.setFixedWidth(dialog.sizeHint().width())
        dialog.exec_()

    def moveFishes(self):
        for fish in self.fishes:
            fish.updatePosition()

    def decreaseCleanliness(self):
        for fish in self.fishes:
            if hasattr(fish, 'aquarium_cleanliness'):
                fish.aquarium_cleanliness -= 1
                if fish.aquarium_cleanliness < 0:
                    fish.aquarium_cleanliness = 0
        self.update_water_cleanliness_label()

    def update_water_cleanliness_label(self):
        return

    def decreaseWaterCleanliness(self):
        for fish in self.fishes:
            fish.water_cleanliness -= 1
            if fish.water_cleanliness < 0:
                fish.water_cleanliness = 0
        self.update_water_cleanliness_label()

    def feedFish(self):
        # Списки начальных координат для каждого изображения еды
        x_values = [200, 450, 700, 900, 1100]
        y_values = [1, 1, 1, 1, 1]

        # Добавляем пять изображений еды на сцену
        for x, y in zip(x_values, y_values):
            food_image_path = os.path.join(
                self.current_directory, "assets", "food.gif")
            food_pixmap = QPixmap(food_image_path)
            food_item = FoodItem(food_pixmap, duration=5000, x=x, y=y)
            self.scene.addItem(food_item)

        # Остальной код остается без изменений
        for fish in self.fishes:
            fish.feedFish()
        self.update_health_label()
        self.update_status_label()
        # Обновляем графический интерфейс
        QApplication.processEvents()

    def update_status_label(self):
        return

    def setupButtons(self):
        self.button1 = QPushButton("Правила", self)
        self.button2 = QPushButton("Накормить рыб", self)
        self.button3 = QPushButton("Почистить аквариум", self)
        self.rules_button = QPushButton("Сменить воду", self)
        self.state_button = QPushButton("Состояние аквариума", self)
        self.button1.clicked.connect(self.showRulesInfo)
        self.button2.clicked.connect(self.feedFish)
        self.button3.clicked.connect(self.clearAquarium)
        self.rules_button.clicked.connect(self.changeWater)
        self.state_button.clicked.connect(self.showAquariumState)
        self.rules_button.clicked.connect(self.changeWater)

        layout = QHBoxLayout()
        layout.addWidget(self.button1)
        layout.addWidget(self.button2)
        layout.addWidget(self.button3)
        layout.addWidget(self.rules_button)
        layout.addWidget(self.state_button)

        widget = QWidget()
        widget.setLayout(layout)
        self.setMenuWidget(widget)

        button_height = HEIGHT_BUTTON
        button_spacing = SPACING_BUTTON
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(button_spacing)

        button_style = (
            "background-color: #008CBA; color: white; border-radius: 24px;"
        )
        button_style = (
            "background-color: #008CBA;"
            "color: white; border-radius: 10px;"
            "font-size: 18px;")
        self.button1.setStyleSheet(button_style)
        self.button1.setStyleSheet(button_style)
        self.button2.setStyleSheet(button_style)
        self.button3.setStyleSheet(button_style)
        self.rules_button.setStyleSheet(button_style)
        self.state_button.setStyleSheet(button_style)

        self.rules_button.move(
            self.rules_button.x(), self.rules_button.y() - 50)

        self.button1.setFixedHeight(button_height)
        self.button2.setFixedHeight(button_height)
        self.button3.setFixedHeight(button_height)
        self.rules_button.setFixedHeight(button_height)
        self.state_button.setFixedHeight(button_height)

    def showEatLabel(self):
        self.hideCurrentLabel()
        self.current_label = None

    def clearAquarium(self):
        # Показываем изображение чистой воды
        self.clean_water_image_item.show()

        # Создаем таймер для скрытия изображения чистой воды
        QTimer.singleShot(2000, self.hideCleanWater)

        # Теперь добавим код по очистке аквариума
        for fish in self.fishes:
            fish.aquarium_cleanliness = AQUARIUM_CLEAN
        # Обновляем графический интерфейс
        QApplication.processEvents()

    def hideCleanWater(self):
        # Скрываем изображение чистой воды
        self.clean_water_image_item.hide()

    def changeWater(self):
        # Удаляем уже существующее изображение воды, если оно есть
        if self.water_item:
            self.scene.removeItem(self.water_item)

        # Создаем новое изображение воды
        water_image_path = os.path.join(
            self.current_directory, "assets", "water.gif")
        water_pixmap = QPixmap(water_image_path)
        water_item = QGraphicsPixmapItem(water_pixmap)
        # Устанавливаем начальные координаты в левый верхний угол
        water_item.setPos(0, 0)
        # Помещаем изображение воды за все другие элементы на сцене
        water_item.setZValue(-1)
        # Режим сглаживания для изображения
        water_item.setTransformationMode(Qt.SmoothTransformation)
        # Устанавливаем размеры изображения равными размерам окна
        water_item.setPixmap(water_pixmap.scaled(self.width(), self.height()))
        self.scene.addItem(water_item)
        # Сохраняем ссылку на новое изображение воды
        self.water_item = water_item

        # Увеличиваем уровень чистоты воды до 100%
        for fish in self.fishes:
            fish.water_cleanliness = 100

        # Создаем таймер для скрытия изображения воды через 5 секунд
        QTimer.singleShot(5000, lambda: self.scene.removeItem(water_item))

    def startWaterChange(self):
        # Устанавливаем изначальное значение чистоты воды
        self.update_water_cleanliness_label()
        self.water_change_timer = QTimer()
        # При срабатывании таймера вызывается метод decreaseWaterCleanliness
        self.water_change_timer.timeout.connect(self.decreaseWaterCleanliness)
        # Таймер срабатывает каждую минуту (60000 миллисекунд)
        self.water_change_timer.start(TIMER_CLEAN_WATER)

    def showRulesInfo(self):
        current_directory = os.path.dirname(os.path.abspath(__file__))
        instructions_file_path = os.path.join(
            current_directory, "assets", "game_instructions.txt")
        with open(instructions_file_path, "r") as file:
            game_instructions = file.read()

        # Создаем сообщение
        dialog = QDialog(self)
        dialog.setWindowTitle("Правила")

        # Устанавливаем стиль шрифта для текста в сообщении
        font = QFont(None, 14)  # None для стандартного (не жирного) шрифта

        # Устанавливаем текст сообщения с переносом строк
        text_label = QLabel(game_instructions.replace("\\n", "\n"))
        text_label.setFont(font)
        text_label.setWordWrap(True)  # Включаем автоматический перенос слов

        layout = QVBoxLayout()
        layout.addWidget(text_label)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.close)
        layout.addWidget(ok_button)

        dialog.setLayout(layout)
        dialog.exec_()

    def showClearLabel(self):
        self.hideCurrentLabel()
        self.current_label = None

    def showWaterLabel(self):
        self.hideCurrentLabel()
        self.current_label = None

    def hideCurrentLabel(self):
        if self.current_label:
            self.current_label.hide()
            self.current_label.deleteLater()

    def resizeEvent(self, event):
        self.view.setGeometry(0, 120, self.width(), self.height()-100)
        super().resizeEvent(event)

    def showAquariumState(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Состояние аквариума")

        layout = QVBoxLayout()

        # Добавляем метку для уровня чистоты воды
        total_water_cleanliness = sum(
            fish.water_cleanliness for fish in self.fishes) // len(
                self.fishes)
        water_cleanliness_label = QLabel()
        water_cleanliness_label.setText(
            f"Уровень чистоты воды: {total_water_cleanliness}%")
        water_cleanliness_label.setFont(QFont(None, 14))
        layout.addWidget(water_cleanliness_label)
        # Добавляем метку для уровня чистоты аквариума
        total_cleanliness = sum(
            fish.aquarium_cleanliness for fish in self.fishes) // len(
                self.fishes)
        cleanliness_label = QLabel(
            f"Уровень чистоты аквариума: {total_cleanliness}%")
        cleanliness_label.setFont(QFont(None, 14))
        layout.addWidget(cleanliness_label)

        ok_button = QPushButton("OK", dialog)
        ok_button.clicked.connect(dialog.close)
        layout.addWidget(ok_button)

        dialog.setLayout(layout)
        dialog.exec_()


def main():
    app = QApplication(sys.argv)
    # Устанавливаем красивый шрифт
    app.setFont(QFont("Arial", 12))
    window = MyWindow()
    window.resize(1720, 1080)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
