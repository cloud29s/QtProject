import sys
import sqlite3
import string
import random
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout,
                             QTableWidget, QTableWidgetItem,
                             QDialog, QLineEdit, QLabel, QMessageBox,
                             QCheckBox, QSpinBox, QGridLayout, QTextEdit)


class PasswordManager(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setWindowTitle('Менеджер паролей')
        self.connect_btn = QPushButton('Подключить')
        self.connect_btn.clicked.connect(self.connect_db)
        self.add_btn = QPushButton('Добавить')
        self.add_btn.clicked.connect(self.add_item)
        self.edit_btn = QPushButton('Изменить')
        self.edit_btn.clicked.connect(self.edit_table)
        self.delete_btn = QPushButton('Удалить')
        self.delete_btn.clicked.connect(self.delete_item)
        self.generate_btn = QPushButton('Сгенерировать')
        self.generate_btn.clicked.connect(self.generate_password)
        self.create_btn = QPushButton('Создать')
        self.create_btn.clicked.connect(self.create_table)
        self.setLayout(self.layout)
        self.db_path = ''
        self.initUI()

    def initUI(self):
        self.table = QTableWidget()
        self.layout.addWidget(self.connect_btn)
        self.layout.addWidget(self.add_btn)
        self.layout.addWidget(self.edit_btn)
        self.layout.addWidget(self.delete_btn)
        self.layout.addWidget(self.generate_btn)
        self.layout.addWidget(self.table)
        self.layout.addWidget(self.create_btn)
        self.setLayout(self.layout)

    def connect_db(self):
        dialog = DatabaseDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.db_path = dialog.get_db_path()
            if self.db_path:
                self.load_data()

    def load_data(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM passwords')
            data = cursor.fetchall()
            conn.close()
            self.table.setRowCount(len(data))
            if not data:
                self.table.setColumnCount(3)
                self.table.setHorizontalHeaderLabels(['website', 'login', 'password'])
                return

            self.table.setColumnCount(len(data[0]))
            self.table.setHorizontalHeaderLabels([i[0] for i in cursor.description])
            for row, row_data in enumerate(data):
                for col, value in enumerate(row_data):
                    self.table.setItem(row, col, QTableWidgetItem(str(value)))
        except sqlite3.Error as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка подключения базы данных: {e}')

    def add_item(self):
        if not self.db_path:
            QMessageBox.warning(self, 'Внимание', 'Подключите сначала базу данных')
            return
        dialog = AddDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            website, login, password = dialog.get_website_login_password()
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('INSERT INTO passwords (website, login, password) VALUES (?, ?, ?)',
                               (website, login, password))
                conn.commit()
                conn.close()
                self.load_data()
            except sqlite3.Error as e:
                QMessageBox.critical(self, 'Ошибка', f'Ошибка добавления элемента: {e}')

    def edit_table(self):
        if not self.db_path:
            QMessageBox.warning(self, 'Внимание', 'Подключите сначала базу данных')
            return
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, 'Внимание', 'База данных пуста')
            return
        dialog = EditDialog(self.table)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            result = dialog.get_edited_cell()
            if result:
                row, col, new_value = result
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute(f'PRAGMA table_info(passwords)')
                    columns = [info[1] for info in cursor.fetchall()]
                    update_column = columns[col]
                    id = self.table.item(row, 0).text()

                    cursor.execute(f'UPDATE passwords SET {update_column} = ? WHERE id = ?', (new_value, id))
                    conn.commit()
                    conn.close()
                    self.load_data()
                except sqlite3.Error as e:
                    QMessageBox.critical(self, 'Ошибка', f'Ошибка обновления базы данных {e}')

    def delete_item(self):
        if not self.db_path:
            QMessageBox.warning(self, 'Внимание', 'Подключите сначала базу данных')
            return
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, 'Внимание', 'База данных пуста')
            return
        dialog = DeleteDialog(self.table)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_row = dialog.get_selected_row()
            if selected_row != -1:
                id = self.table.item(selected_row, 0).text()
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM passwords WHERE id = ?', (id,))
                    conn.commit()
                    conn.close()
                    self.load_data()
                except sqlite3.Error as e:
                    QMessageBox.critical(self, 'Ошибка', f'Ошибка при удалении объекта: {e}')

    def generate_password(self):
        dialog = GenerateDialog()
        dialog.exec()

    def create_table(self):
        dialog = CreateTable()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            db_name = dialog.get_db_name()
            if db_name:
                try:
                    conn = sqlite3.connect(db_name)
                    cursor = conn.cursor()
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS passwords (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            website TEXT,
                            login TEXT,
                            password TEXT
                        )
                    ''')
                    conn.commit()
                    print(f"База данных '{db_name}' и таблица 'passwords' успешно созданы.")
                except sqlite3.Error as e:
                    print(f'Ошибка при создании базы данных: {e}')
                finally:
                    if conn:
                        conn.close()


class DatabaseDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Подключить базу данных')
        self.layout = QVBoxLayout()
        self.label = QLabel('Введите название файла')
        self.path_edit = QLineEdit()
        self.connect_btn = QPushButton('Подключить')
        self.connect_btn.clicked.connect(self.accept)
        self.db_path = ''
        self.initUI()

    def initUI(self):
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.path_edit)
        self.layout.addWidget(self.connect_btn)
        self.setLayout(self.layout)

    def get_db_path(self):
        return self.path_edit.text()

class AddDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Добавить элемент')
        self.layout = QVBoxLayout()
        self.website_label = QLabel('Сайт:')
        self.website_edit = QLineEdit()
        self.login_label = QLabel('Логин:')
        self.login_edit = QLineEdit()
        self.password_label = QLabel('Пароль:')
        self.password_edit = QLineEdit()
        self.add_btn = QPushButton('Добавить')
        self.add_btn.clicked.connect(self.accept)
        self.initUI()

    def initUI(self):
        self.layout.addWidget(self.website_label)
        self.layout.addWidget(self.website_edit)
        self.layout.addWidget(self.login_label)
        self.layout.addWidget(self.login_edit)
        self.layout.addWidget(self.password_label)
        self.layout.addWidget(self.password_edit)
        self.layout.addWidget(self.add_btn)
        self.setLayout(self.layout)

    def get_website_login_password(self):
        return (self.website_edit.text(), self.login_edit.text(), self.password_edit.text())

class EditDialog(QDialog):
    def __init__(self, table_widget):
        super().__init__()
        self.setWindowTitle('Изменить ячейку')
        self.table_widget = table_widget
        self.layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setRowCount(self.table_widget.rowCount())
        self.table.setColumnCount(self.table_widget.columnCount())
        self.headers = []
        for x in range(self.table_widget.columnCount()):
            self.headers.append(self.table_widget.horizontalHeaderItem(x).text())
        self.table.setHorizontalHeaderLabels(self.headers)
        for row in range(self.table_widget.rowCount()):
            for col in range(self.table_widget.columnCount()):
                item = QTableWidgetItem(self.table_widget.item(row, col).text())
                self.table.setItem(row, col, item)
        self.edit_btn = QPushButton('Изменить')
        self.edit_btn.clicked.connect(self.accept)
        self.selected_row = -1
        self.selected_col = -1
        self.table.cellClicked.connect(self.select_cell)
        self.initUI()

    def initUI(self):
        self.layout.addWidget(self.table)
        self.layout.addWidget(self.edit_btn)
        self.setLayout(self.layout)

    def select_cell(self, row, col):
        self.selected_row = row
        self.selected_col = col

    def get_edited_cell(self):
        if self.selected_row != -1 and self.selected_col != -1:
            return (self.selected_row, self.selected_col, self.table.item(self.selected_row, self.selected_col).text())
        return None

class CreateTable(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Создать базу данных')
        self.layout = QVBoxLayout()
        self.label = QLabel('Введите название для базы данных')
        self.name_input = QLineEdit()
        self.create_btn = QPushButton('Создать')
        self.create_btn.clicked.connect(self.accept)
        self.db_name = ''
        self.initUI()

    def initUI(self):
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.name_input)
        self.layout.addWidget(self.create_btn)
        self.setLayout(self.layout)

    def get_db_name(self):
        return self.name_input.text()


class GenerateDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Сгенерировать пароль')
        self.setGeometry(200, 200, 400, 300)

        self.layout = QGridLayout()
        self.length_label = QLabel('Длина:')
        self.length_spin = QSpinBox()
        self.length_spin.setMinimum(8)
        self.length_spin.setMaximum(128)
        self.length_spin.setValue(16)
        self.uppercase_check = QCheckBox('Использовать нижний регистр')
        self.uppercase_check.setChecked(True)
        self.lowercase_check = QCheckBox('Использовать нижний регистр')
        self.lowercase_check.setChecked(True)
        self.digits_check = QCheckBox('Использовать цифры')
        self.digits_check.setChecked(True)
        self.punctuation_check = QCheckBox('Использовать знаки')
        self.punctuation_check.setChecked(True)
        self.cyrillic_check = QCheckBox('Использовать кириллицу')
        self.cyrillic_check.setChecked(True)
        self.generate_button = QPushButton('Сгенерировать')
        self.generate_button.clicked.connect(self.generate_password)
        self.result_edit = QTextEdit()
        self.result_edit.setReadOnly(True)
        self.copy_button = QPushButton('Скопировать пароль')
        self.copy_button.clicked.connect(self.copy_password)
        self.setLayout(self.layout)
        self.password = None
        self.initUI()

    def initUI(self):
        self.layout.addWidget(self.length_label, 0, 0)
        self.layout.addWidget(self.length_spin, 0, 1)
        self.layout.addWidget(self.uppercase_check, 1, 0, 1, 2)
        self.layout.addWidget(self.lowercase_check, 2, 0, 1, 2)
        self.layout.addWidget(self.digits_check, 3, 0, 1, 2)
        self.layout.addWidget(self.punctuation_check, 4, 0, 1, 2)
        self.layout.addWidget(self.cyrillic_check, 5, 0, 1, 2)
        self.layout.addWidget(self.generate_button, 6, 0, 1, 2)
        self.layout.addWidget(self.result_edit, 7, 0, 1, 2)
        self.layout.addWidget(self.copy_button, 8, 0, 1, 2)

    def generate_password(self):
        length = self.length_spin.value()
        include_uppercase = self.uppercase_check.isChecked()
        include_lowercase = self.lowercase_check.isChecked()
        include_digits = self.digits_check.isChecked()
        include_punctuation = self.punctuation_check.isChecked()
        include_cyrillic = self.cyrillic_check.isChecked()

        alphabet = ''
        if include_uppercase:
            alphabet += string.ascii_uppercase
        if include_lowercase:
            alphabet += string.ascii_lowercase
        if include_digits:
            alphabet += string.digits
        if include_punctuation:
            alphabet += string.punctuation
        if include_cyrillic and include_uppercase:
            alphabet += 'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
        if include_cyrillic and include_lowercase:
            alphabet += 'абвгдежзийклмнопрстуфхцчшщъыьэюя'
        if not alphabet:
            QMessageBox.warning(self, 'Внимание', 'Выберите хотя бы один чекбокс')
            return
        self.password = ''
        for _ in range(length):
            self.password += random.choice(alphabet)
        self.result_edit.setText(self.password)

    def copy_password(self):
        if self.password:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.password)
            QMessageBox.information(self, 'Успешно', 'Пароль скопирован в буфер обмена')

    def get_password_settings(self):
        length = self.length_spin.value()
        include_uppercase = self.uppercase_check.isChecked()
        include_lowercase = self.lowercase_check.isChecked()
        include_digits = self.digits_check.isChecked()
        include_punctuation = self.punctuation_check.isChecked()
        include_cyrillic = self.cyrillic_check.isChecked()
        return length, include_uppercase, include_lowercase, include_digits, include_punctuation, include_cyrillic


class DeleteDialog(QDialog):
    def __init__(self, table_widget):
        super().__init__()
        self.setWindowTitle('Удалить строку')
        self.table_widget = table_widget
        self.layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setRowCount(self.table_widget.rowCount())
        self.table.setColumnCount(self.table_widget.columnCount())
        self.headers = []
        for x in range(self.table_widget.columnCount()):
            self.headers.append(self.table_widget.horizontalHeaderItem(x).text())
        self.table.setHorizontalHeaderLabels(self.headers)
        for row in range(self.table_widget.rowCount()):
            for col in range(self.table_widget.columnCount()):
                item = QTableWidgetItem(self.table_widget.item(row, col).text())
                self.table.setItem(row, col, item)

        self.delete_btn = QPushButton('Delete')
        self.delete_btn.clicked.connect(self.accept)
        self.layout.addWidget(self.table)
        self.layout.addWidget(self.delete_btn)
        self.setLayout(self.layout)
        self.selected_row = -1

        self.table.cellClicked.connect(self.select_cell)

    def select_cell(self, row):
        self.selected_row = row

    def get_selected_row(self):
        return self.selected_row


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PasswordManager()
    window.show()
    sys.exit(app.exec())
