import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton,
                             QGraphicsPixmapItem, QGraphicsScene,
                             QGraphicsView, QFrame, QHBoxLayout, QWidget,
                             QVBoxLayout, QDialog)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QFont, QTransform, QBrush
import os

TIMER_CLEAN_AQUARIUM = 120000
TIMER_CLEAN_WATER = 60000
TIMER_FISH_POSITION = 60000
TIMER_UPDATE_HEALTH = 16
FISH_HEALTH = 100
WATER_CLEAN = 100
AQUARIUM_CLEAN = 100
FISH_HUNGER = 100
FISH_BASE_HUNGER = 0
FISH_SPEED = 1.2
HEIGHT_BUTTON = 90
SPACING_BUTTON = 20


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
        print(f"{self.fish_type} здоровье: {self.health}%")

        # Обновление метки на интерфейсе, после изменения здоровья
        if self.scene() and self.scene().views():
            window = self.scene().views()[0].window()
            window.update_health_label()

    def updateStatus(self):  # Уменьшение здоровья рыбам
        self.decreaseHealth()

        self.hunger += 1  # Увеличение голода рыбам
        if self.hunger > FISH_HUNGER:
            self.hunger = FISH_HUNGER
        print(
            f"{self.fish_type} здоровье: {self.health}%, голод: {self.hunger}%"
            )
        # Обновление метки на интрерфейсе, после изменения голода и здоровья
        if self.scene() and self.scene().views():
            window = self.scene().views()[0].window()
            window.update_status_label()

    def getHungerLevel(self):  # Голод рыб
        return self.hunger

    def feedFish(self):
        self.health = min(100, self.health + 100)  # Увеличение здоровья рыбы
        self.hunger = 0  # Сбрасывание уровня голода
        print(
            f"{self.fish_type.capitalize()} покормлено. "
            f"Здоровье: {self.health}%, голод: {self.hunger}%"
        )
        if self.fish_type == "carp":
            print(self.description)

    def mousePressEvent(self, event):
        if self.pixmap().toImage() == QPixmap(
                "assets/music.gif").toImage():
            self.musicClicked.emit()
            return
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
        self.current_directory = os.path.dirname(os.path.abspath(__file__))
        current_directory = os.path.dirname(os.path.abspath(__file__))
        okun_description_path = os.path.join(
            current_directory, "assets", "Okun_description.txt")
        shuka_description_path = os.path.join(
            current_directory, "assets", "Shuka_description.txt")
        carp_description_path = os.path.join(
            current_directory, "assets", "Carp_description.txt")
        vobla_description_path = os.path.join(
            current_directory, "assets", "Vobla_description.txt")
        seld_description_path = os.path.join(
            current_directory, "assets", "Seld_description.txt")
        self.setWindowTitle("Эмулятор Аквариума")
        self.setFixedSize(1525, 950)  # Фиксированный размер окна
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, 1525, 899)  # Установка размеров сцены
        self.view = QGraphicsView(self.scene, self)
        self.setCentralWidget(self.view)
        background_image_path = os.path.join(
            current_directory, "assets", "main.gif")
        background_pixmap = QPixmap(background_image_path)
        background_brush = QBrush(background_pixmap)
        self.scene.setBackgroundBrush(background_brush)

        self.view = QGraphicsView(self.scene, self)
        self.setCentralWidget(self.view)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.view.setFrameShape(QFrame.NoFrame)

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
                os.path.join(current_directory, "assets", "fish1.gif"),
                "Окунь",
                Okun_description),
            MovingFish(
                500, 300, 1600, 900,
                os.path.join(current_directory, "assets", "fish2.gif"),
                "Щука",
                Shuka_description),
            MovingFish(
                700, 500, 1600, 900,
                os.path.join(current_directory, "assets", "fish3.gif"),
                "Карп",
                Carp_description),
            MovingFish(
                1100, 50, 1600, 900,
                os.path.join(current_directory, "assets", "fish4.gif"),
                "Вобла",
                Vobla_description),
            MovingFish(
                500, 50, 1600, 900,
                os.path.join(current_directory, "assets", "fish5.gif"),
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
            if fish.pixmap().toImage() != QPixmap(
                    "/Users/mvideomvideo/Desktop/Python/music.gif").toImage():
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
        for fish in self.fishes:
            fish.feedFish()
        self.update_health_label()
        self.update_status_label()

    def update_status_label(self):
        return

    def spawnFood(self):
        # Путь к изображению еды
        food_image_path = os.path.join(
            self.current_directory, "assets", "food.gif")
        start_positions = [
            (100, 0), (500, 200), (900, 0), (300, 400), (900, 400)]
        for start_pos in start_positions:
            food_item = QGraphicsPixmapItem(QPixmap(food_image_path))
            food_item.setPos(*start_pos)
            self.scene.addItem(food_item)
            QTimer.singleShot(
                5000, lambda item=food_item: self.removeFood(item))
            timer = QTimer()
            timer.timeout.connect(
                lambda item=food_item: self.updateFoodPosition(item))
            timer.start(100)

    def updateFoodPosition(self, food_item):
        current_x = food_item.x()
        current_y = food_item.y()

        # Скорость движения корма
        food_speed = 5

        # Новые координаты корма с учетом скорости падения
        new_y = current_y + food_speed

        # Перемещаем корм по вертикали
        food_item.setPos(current_x, new_y)

        # Проверяем, достиг ли корм нижней границы сцены
        if new_y >= self.scene.sceneRect().bottom():
            # Если да, удаляем корм из сцены
            self.scene.removeItem(food_item)

    def removeFood(self, food_item):
        self.scene.removeItem(food_item)

    def setupButtons(self):
        self.button1 = QPushButton("Правила", self)
        self.button2 = QPushButton("Накормить рыб", self)
        self.button2.clicked.connect(self.spawnFood)
        self.button3 = QPushButton("Почистить аквариум", self)
        self.rules_button = QPushButton("Сменить воду", self)
        self.state_button = QPushButton("Состояние аквариума", self)
        self.button1.clicked.connect(self.showRulesInfo)
        self.button2.clicked.connect(self.feedFish)
        self.button3.clicked.connect(self.clearAquarium)
        self.button2.clicked.connect(self.spawnFood)
        self.button2.clicked.connect(self.feedFish)
        self.rules_button.clicked.connect(self.changeWater)
        self.state_button.clicked.connect(self.showAquariumState)
        self.rules_button.clicked.connect(self.changeWater)
        self.rules_button.clicked.connect(self.showAquariumState)

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
        new_label = QLabel("Накормить рыб", self)
        new_label.setGeometry(100, 150, 200, 50)
        new_label.setStyleSheet("color: black;")
        new_label.show()
        self.current_label = new_label

    def clearAquarium(self):
        for fish in self.fishes:
            fish.aquarium_cleanliness = AQUARIUM_CLEAN
        self.showAquariumState()

    def changeWater(self):
        for fish in self.fishes:
            fish.water_cleanliness = WATER_CLEAN
        self.update_water_cleanliness_label()
        self.startWaterChange()

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
        new_label = QLabel("Почистить аквариум", self)
        new_label.setGeometry(100, 150, 200, 50)
        new_label.setStyleSheet("color: black;")
        new_label.show()
        self.current_label = new_label

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
    window.resize(1400, 900)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
