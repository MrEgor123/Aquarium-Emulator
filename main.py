import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton,
                             QGraphicsPixmapItem, QGraphicsScene,
                             QGraphicsView, QFrame, QHBoxLayout, QWidget,
                             QVBoxLayout, QMessageBox, QDialog)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QEvent, QRectF, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPixmap, QFont, QTransform, QBrush, QColor, QPalette, QLinearGradient

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


class FoodItem(QGraphicsPixmapItem):
    """Создает объект корма для рыб на сцене."""

    def __init__(self, pixmap, duration=5000, x=0, y=0, parent=None):
        super().__init__(pixmap, parent)
        self.duration = duration
        self.setPos(x, y)

        self.fall_timer = QTimer()
        self.fall_timer.timeout.connect(self.fall)
        self.fall_timer.start(50)

    def fall(self):
        """Опускает корм вниз, удаляя его при достижении дна."""
        current_pos = self.pos()
        distance = 899 - current_pos.y()
        speed = distance / (self.duration / 50)
        new_y = current_pos.y() + speed
        self.setPos(current_pos.x(), new_y)
        if new_y >= 899:
            self.fall_timer.stop()
            self.scene().removeItem(self)


class MovingFish(QGraphicsPixmapItem):
    musicClicked = pyqtSignal()

    def __init__(self, x, y, scene_width, scene_height,
                 pixmap_path, fish_type, description, scale_factor=1):
        """Создает объект рыбы, который может двигаться по сцене."""
        super().__init__()
        self.direction_x = 1
        self.direction_y = 1
        self.scene_width = scene_width
        self.scene_height = scene_height
        self.original_pixmap = QPixmap(pixmap_path)
        self.label_visible = False
        self.fish_type = fish_type
        self.health = FISH_HEALTH
        self.hunger = FISH_BASE_HUNGER
        self.description = description
        self.water_cleanliness = WATER_CLEAN
        self.aquarium_cleanliness = AQUARIUM_CLEAN

        pixmap = QPixmap(pixmap_path)
        pixmap = pixmap.scaled(int(pixmap.width() * scale_factor),
                               int(pixmap.height() * scale_factor))
        self.setPixmap(pixmap)
        self.setPos(x, y)
        self.setAcceptHoverEvents(True)

        self.timer = QTimer()
        self.timer.timeout.connect(self.updateStatus)
        self.timer.start(TIMER_FISH_POSITION)

    def decreaseHealth(self):
        """Уменьшает здоровье рыбы на 2 единицы."""
        self.health -= 2
        self.health = max(0, self.health)

    def updateStatus(self):
        """Обновляет здоровье и голод рыбы."""
        self.decreaseHealth()
        self.hunger += 1
        self.hunger = min(FISH_HUNGER, self.hunger)

    def getHungerLevel(self):
        """Возвращает уровень голода рыбы."""
        return self.hunger

    def feedFish(self):
        """Кормит рыбу, увеличивая ее здоровье и сбрасывая голод."""
        self.health = min(100, self.health + 100)
        self.hunger = 0

    def mousePressEvent(self, event):
        """Обрабатывает событие нажатия мыши на рыбу."""
        super().mousePressEvent(event)
        window = self.scene().views()[0].window()
        window.showFishInfo(self)

    def updatePosition(self):
        """Обновляет позицию рыбы, двигая ее по сцене."""
        current_x = self.x()
        current_y = self.y()
        new_x = current_x + self.direction_x * FISH_SPEED
        new_y = current_y + self.direction_y * FISH_SPEED
        if new_x < 0:
            new_x = 0
            self.direction_x *= -1
        elif new_x > self.scene_width - self.pixmap().width():
            new_x = self.scene_width - self.pixmap().width()
            self.direction_x *= -1
        if new_y < 0:
            new_y = 0
            self.direction_y *= -1
        elif new_y > self.scene_height - self.pixmap().height():
            new_y = self.scene_height - self.pixmap().height()
            self.direction_y *= -1
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
    def __init__(self):
        super().__init__()
        self.water_item = None
        self.food_items = []
        self.current_directory = os.path.dirname(os.path.abspath(__file__))

        # Настройки окна
        self.setWindowTitle("Эмулятор Аквариума")
        self.setFixedSize(1725, 950)

        # Создание сцены
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, 1525, 800)

        # Создание вида
        self.view = QGraphicsView(self.scene, self)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.view.setFrameShape(QFrame.NoFrame)
        self.view.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # Установка фона
        self.background_image_path = os.path.join(
            self.current_directory, "assets", "main.gif")
        self.background_pixmap = QPixmap(self.background_image_path)
        background_brush = QBrush(self.background_pixmap)
        self.scene.setBackgroundBrush(background_brush)

        # Добавление изображения для очистки воды
        self.clean_image_path = os.path.join(
            self.current_directory, "assets", "clean.gif")
        clean_pixmap = QPixmap(self.clean_image_path)
        clean_pixmap = clean_pixmap.scaled(750, 750)
        self.clean_water_image_item = QGraphicsPixmapItem(clean_pixmap)
        self.clean_water_image_item.setPos(350, 100)
        self.clean_water_image_item.hide()
        self.scene.addItem(self.clean_water_image_item)

        # Загрузка описаний рыб
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

        # Создание рыб
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

        # Добавление рыб на сцену
        for fish in self.fishes:
            self.scene.addItem(fish)

        # Создание кнопок
        self.setupButtons()

        # Создание меток
        self.current_label = None
        self.health_label = QLabel(self)
        self.health_label.setGeometry(1300, 50, 200, 50)
        self.health_label.setStyleSheet(
            "color: white; font-weight: bold;")
        self.update_health_label()
        self.hunger_labels = []
        for i, fish in enumerate(self.fishes):
            hunger_label = QLabel(self)
            hunger_label.setGeometry(100, 250 + i * 100, 200, 50)
            hunger_label.setStyleSheet(
                "color: white; font-weight: bold;")
            self.hunger_labels.append(hunger_label)

        self.water_cleanliness_label = QLabel(self)
        self.water_cleanliness_label.setGeometry(1300, 150, 200, 50)
        self.water_cleanliness_label.setStyleSheet(
            "color: white; font-weight: bold;")
        self.update_water_cleanliness_label()

        # Создание таймеров
        self.cleanliness_timer = QTimer(self)
        self.cleanliness_timer.timeout.connect(self.decreaseCleanliness)
        self.cleanliness_timer.start(TIMER_CLEAN_AQUARIUM)

        self.water_change_timer = QTimer(self)
        self.water_change_timer.timeout.connect(
            self.decreaseWaterCleanliness)
        self.water_change_timer.start(TIMER_CLEAN_WATER)

        self.feed_timer = QTimer(self)
        self.feed_timer.setSingleShot(True)
        self.feed_timer.timeout.connect(self.enableFeedButton)

        # Установка layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.button_widget.setParent(central_widget)
        main_layout.addWidget(self.button_widget)
        main_layout.addWidget(self.view)

        self.button_widget.show()

        # Установка градиентного фона
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(0, 123, 186))
        self.setPalette(palette)

    def update_health_label(self):
        """Обновляет метку здоровья."""
        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.moveFishes)
        self.move_timer.start(TIMER_UPDATE_HEALTH)

    def showFishInfo(self, fish):
        """Показывает диалоговое окно с информацией о рыбе."""
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
        """Двигает рыб по сцене."""
        for fish in self.fishes:
            fish.updatePosition()

    def decreaseCleanliness(self):
        """Уменьшает чистоту аквариума для всех рыб."""
        for fish in self.fishes:
            fish.aquarium_cleanliness -= 1
            fish.aquarium_cleanliness = max(0, fish.aquarium_cleanliness)
        self.update_water_cleanliness_label()

    def update_water_cleanliness_label(self):
        """Обновляет метку чистоты воды."""
        return

    def decreaseWaterCleanliness(self):
        """Уменьшает чистоту воды для всех рыб."""
        for fish in self.fishes:
            fish.water_cleanliness -= 1
            fish.water_cleanliness = max(0, fish.water_cleanliness)
        self.update_water_cleanliness_label()

    def feedFish(self):
        """Кормит рыб, создавая на сцене объекты корма."""
        if not self.feed_timer.isActive():
            x_values = [200, 450, 700, 900, 1100]
            y_values = [1, 1, 1, 1, 1]

            for x, y in zip(x_values, y_values):
                food_image_path = os.path.join(
                    self.current_directory, "assets", "food.gif")
                food_pixmap = QPixmap(food_image_path)
                food_item = FoodItem(food_pixmap, duration=5000, x=x, y=y)
                self.scene.addItem(food_item)

            for fish in self.fishes:
                fish.feedFish()
            self.update_health_label()
            self.update_status_label()
            QApplication.processEvents()

            self.button2.setEnabled(False)
            self.feed_timer.start(5000)

    def enableFeedButton(self):
        """Включает кнопку "Накормить рыб" после интервала."""
        self.button2.setEnabled(True)

    def update_status_label(self):
        """Обновляет метку статуса."""
        return

    def setupButtons(self):
        """Создает и настраивает кнопки интерфейса."""
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

        layout = QHBoxLayout()
        layout.addWidget(self.button1)
        layout.addWidget(self.button2)
        layout.addWidget(self.button3)
        layout.addWidget(self.rules_button)
        layout.addWidget(self.state_button)

        self.button_widget = QWidget(self)
        self.button_widget.setLayout(layout)

        button_height = HEIGHT_BUTTON
        button_spacing = SPACING_BUTTON
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(button_spacing)

        button_style = """
            QPushButton {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                  stop: 0 #007bff, stop: 1 #0056b3);
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                  stop: 0 #0069d9, stop: 1 #004aa3);
            }
            QPushButton:pressed {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                  stop: 0 #005cbf, stop: 1 #00347a);
            }
        """
        self.button1.setStyleSheet(button_style)
        self.button2.setStyleSheet(button_style)
        self.button3.setStyleSheet(button_style)
        self.rules_button.setStyleSheet(button_style)
        self.state_button.setStyleSheet(button_style)

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
        """Очищает аквариум, показывая изображение чистой воды."""
        self.clean_water_image_item.show()
        QTimer.singleShot(2000, self.hideCleanWater)

        for fish in self.fishes:
            fish.aquarium_cleanliness = AQUARIUM_CLEAN
        QApplication.processEvents()

    def hideCleanWater(self):
        """Скрывает изображение чистой воды."""
        self.clean_water_image_item.hide()

    def changeWater(self):
        """Сменяет воду в аквариуме."""
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
        with open(instructions_file_path, "r") as file:
            game_instructions = file.read()

        dialog = QDialog(self)
        dialog.setWindowTitle("Правила")

        # Устанавливаем стиль шрифта для текста в сообщении
        font = QFont(None, 14)

        # Устанавливаем текст сообщения с переносом строк
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
        """Скрывает текущую метку."""
        if self.current_label:
            self.current_label.hide()
            self.current_label.deleteLater()

    def resizeEvent(self, event):
        """Обрабатывает событие изменения размера окна."""
        super().resizeEvent(event)

        if self.scene.backgroundBrush().texture():
            scaled_pixmap = self.background_pixmap.scaled(
                self.width(), self.height(),
                Qt.KeepAspectRatioByExpanding
            )
            self.scene.setBackgroundBrush(QBrush(scaled_pixmap))

        self.button_widget.setGeometry(
            0, 0, self.width(), self.button_widget.height())

        self.updateFishBoundaries()

    def updateFishBoundaries(self):
        """Обновляет границы для движения рыб."""
        bg_rect = self.background_pixmap.rect()
        bg_scene_rect = self.view.mapToScene(bg_rect).boundingRect()
        for fish in self.fishes:
            fish.scene_width = bg_scene_rect.width()
            fish.scene_height = bg_scene_rect.height()

    def showAquariumState(self):
        """Показывает диалоговое окно с состоянием аквариума."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Состояние аквариума")

        layout = QVBoxLayout()

        # Вычисляем средний уровень чистоты воды
        total_water_cleanliness = sum(
            fish.water_cleanliness for fish in self.fishes) // len(
                self.fishes)
        # Создаем метку для уровня чистоты воды
        water_cleanliness_label = QLabel()
        water_cleanliness_label.setText(
            f"Уровень чистоты воды: {total_water_cleanliness}%")
        water_cleanliness_label.setFont(QFont(None, 14))
        layout.addWidget(water_cleanliness_label)

        # Вычисляем средний уровень чистоты аквариума
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
        if obj == self.button_widget and event.type() == QEvent.MouseButtonPress:
            mouse_pos = event.pos()
            for button in [self.button1, self.button2, self.button3,
                           self.rules_button, self.state_button]:
                if button.geometry().contains(mouse_pos):
                    button.click()
                    return True
        return super().eventFilter(obj, event)


def main():
    """Запускает главное приложение."""
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 12))
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
