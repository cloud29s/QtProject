import sys
import sqlite3
import string
import random

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout,
                             QTableWidget, QTableWidgetItem, QButtonGroup,
                             QDialog, QLineEdit, QLabel, QMessageBox,
                             QCheckBox, QSpinBox, QGridLayout, QTextEdit, QInputDialog, QRadioButton)


class StartMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.dict = {

        }
        icon = QIcon('Capy.jpg')
        self.setWindowIcon(icon)
        self.layout = QVBoxLayout()
        self.setWindowTitle('Выбор языка/Choose language')
        self.en_btn = QRadioButton('English', self)
        self.ru_btn = QRadioButton('Русский', self)
        self.lang_grp = QButtonGroup(self)
        self.lang_grp.addButton(self.en_btn)
        self.lang_grp.addButton(self.ru_btn)
        self.lang_btn = QPushButton('Выбрать/Choose')
        self.lang_btn.clicked.connect(self.choose_lang)
        self.initUI()

    def initUI(self):
        self.layout.addWidget(self.ru_btn)
        self.layout.addWidget(self.en_btn)
        self.layout.addWidget(self.lang_btn)
        self.setLayout(self.layout)

    def choose_lang(self):
        self.rus = False
        self.eng = False
        for obj in self.lang_grp.buttons():
            if obj.isChecked():
                if obj.text() == 'English':
                    self.eng = True
                elif obj.text() == 'Русский':
                    self.rus = True

        if self.rus:
            self.close()
            with open('RU.txt', encoding='UTF-8') as f:
                data = f.readlines()
            data = ''.join(data)
            data = data.split('\n')
            for x in data:
                x = x.split(':')
                self.dict[int(x[0])] = x[1][1:len(x[1]) - 1]
            dialog = PasswordManager(self.dict)
            dialog.exec()
        elif self.eng:
            self.close()
            with open('EN.txt', encoding='UTF-8') as f:
                data = f.readlines()
            data = ''.join(data)
            data = data.split('\n')
            for x in data:
                x = x.split(':')
                self.dict[int(x[0])] = x[1][1:len(x[1]) - 1]
            dialog = PasswordManager(self.dict)
            dialog.exec()
        else:
            QMessageBox.warning(self, 'Внимание/Warning', 'Выберите язык/Choose language')
            return


class PasswordManager(QDialog):
    def __init__(self, dict):
        super().__init__()
        icon = QIcon('Capy.jpg')
        self.setWindowIcon(icon)
        self.dict = dict
        self.layout = QVBoxLayout()
        self.setWindowTitle(dict[1])
        self.connect_btn = QPushButton(self.dict[2])
        self.connect_btn.clicked.connect(self.connect_db)
        self.add_btn = QPushButton(self.dict[3])
        self.add_btn.clicked.connect(self.add_item)
        self.edit_btn = QPushButton(self.dict[4])
        self.edit_btn.clicked.connect(self.edit_table)
        self.delete_btn = QPushButton(self.dict[5])
        self.delete_btn.clicked.connect(self.delete_item)
        self.generate_btn = QPushButton(self.dict[6])
        self.generate_btn.clicked.connect(self.generate_password)
        self.create_btn = QPushButton(self.dict[7])
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
        name, ok_pressed = QInputDialog.getText(self, self.dict[8],
                                                self.dict[9])
        icon = QIcon('Capy.jpg')
        self.setWindowIcon(icon)
        self.db_path = name
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
            QMessageBox.critical(self, self.dict[10], f'{self.dict[11]} {e}')

    def add_item(self):
        if not self.db_path:
            QMessageBox.warning(self, self.dict[12], self.dict[13])
            return
        dialog = AddDialog(self.dict)
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
                QMessageBox.critical(self, self.dict[10], f'{self.dict[15]} {e}')

    def edit_table(self):
        if not self.db_path:
            QMessageBox.warning(self, self.dict[12], self.dict[13])
            return
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, self.dict[12], self.dict[14])
            return
        dialog = EditDialog(self.table, self.dict)
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
                    QMessageBox.critical(self, self.dict[10], f'{self.dict[16]} {e}')

    def delete_item(self):
        if not self.db_path:
            QMessageBox.warning(self, self.dict[12], self.dict[13])
            return
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, self.dict[12], self.dict[14])
            return
        dialog = DeleteDialog(self.table, self.dict)
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
                    QMessageBox.critical(self, self.dict[10], f'{self.dict[17]} {e}')

    def generate_password(self):
        dialog = GenerateDialog(self.dict)
        dialog.exec()

    def create_table(self):
        dialog = CreateTable(self.dict)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.db_path = dialog.get_db_name()
            if self.db_path:
                try:
                    conn = sqlite3.connect(self.db_path)
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
                    print(f'{self.dict[19]} {self.db_path} {self.dict[20]}')
                except sqlite3.Error as e:
                    print(f'{self.dict[21]} {e}')
                finally:
                    if conn:
                        conn.close()

        self.load_data()


class AddDialog(QDialog):
    def __init__(self, dict):
        super().__init__()
        self.dict = dict
        icon = QIcon('Capy.jpg')
        self.setWindowIcon(icon)
        self.setWindowTitle(self.dict[22])
        self.layout = QVBoxLayout()
        self.website_label = QLabel(self.dict[23])
        self.website_edit = QLineEdit()
        self.login_label = QLabel(self.dict[24])
        self.login_edit = QLineEdit()
        self.password_label = QLabel(self.dict[25])
        self.password_edit = QLineEdit()
        self.add_btn = QPushButton(self.dict[3])
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
    def __init__(self, table_widget, dict):
        super().__init__()
        self.dict = dict
        icon = QIcon('Capy.jpg')
        self.setWindowIcon(icon)
        self.setWindowTitle(self.dict[18])
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
        self.edit_btn = QPushButton(self.dict[4])
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
    def __init__(self, dict):
        super().__init__()
        self.dict = dict
        self.setWindowTitle(self.dict[26])
        self.layout = QVBoxLayout()
        self.label = QLabel(self.dict[27])
        self.name_input = QLineEdit()
        self.create_btn = QPushButton(self.dict[7])
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
    def __init__(self, dict):
        super().__init__()
        self.dict = dict
        icon = QIcon('Capy.jpg')
        self.setWindowIcon(icon)
        self.setWindowTitle(self.dict[28])
        self.setGeometry(400, 400, 300, 300)

        self.layout = QGridLayout()
        self.length_label = QLabel(self.dict[29])
        self.length_spin = QSpinBox()
        self.length_spin.setMinimum(8)
        self.length_spin.setMaximum(128)
        self.length_spin.setValue(16)
        self.uppercase_check = QCheckBox(self.dict[30])
        self.uppercase_check.setChecked(True)
        self.lowercase_check = QCheckBox(self.dict[31])
        self.lowercase_check.setChecked(True)
        self.digits_check = QCheckBox(self.dict[32])
        self.digits_check.setChecked(True)
        self.punctuation_check = QCheckBox(self.dict[33])
        self.punctuation_check.setChecked(True)
        self.latin_check = QCheckBox(self.dict[34])
        self.latin_check.setChecked(True)
        self.cyrillic_check = QCheckBox(self.dict[35])
        self.cyrillic_check.setChecked(True)
        self.generate_button = QPushButton(self.dict[6])
        self.generate_button.clicked.connect(self.generate_password)
        self.result_edit = QTextEdit()
        self.result_edit.setReadOnly(True)
        self.copy_button = QPushButton(self.dict[36])
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
        self.layout.addWidget(self.latin_check, 5, 0, 1, 2)
        self.layout.addWidget(self.cyrillic_check, 6, 0, 1, 2)
        self.layout.addWidget(self.generate_button, 7, 0, 1, 2)
        self.layout.addWidget(self.result_edit, 8, 0, 1, 2)
        self.layout.addWidget(self.copy_button, 9, 0, 1, 2)

    def generate_password(self):
        length = self.length_spin.value()
        include_uppercase = self.uppercase_check.isChecked()
        include_lowercase = self.lowercase_check.isChecked()
        include_digits = self.digits_check.isChecked()
        include_punctuation = self.punctuation_check.isChecked()
        include_latin = self.latin_check.isChecked()
        include_cyrillic = self.cyrillic_check.isChecked()

        alphabet = ''
        if include_latin:
            if include_uppercase:
                alphabet += string.ascii_uppercase
            if include_lowercase:
                alphabet += string.ascii_lowercase
        if include_digits:
            alphabet += string.digits
        if include_punctuation:
            alphabet += string.punctuation
        if include_cyrillic:
            if include_uppercase:
                alphabet += 'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
            if include_lowercase:
                alphabet += 'абвгдежзийклмнопрстуфхцчшщъыьэюя'
        if not alphabet:
            QMessageBox.warning(self, self.dict[12], self.dict[37])
            return
        self.password = ''
        for _ in range(length):
            self.password += random.choice(alphabet)
        self.result_edit.setText(self.password)

    def copy_password(self):
        if self.password:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.password)
            QMessageBox.information(self, self.dict[38], self.dict[39])

    def get_password_settings(self):
        length = self.length_spin.value()
        include_uppercase = self.uppercase_check.isChecked()
        include_lowercase = self.lowercase_check.isChecked()
        include_digits = self.digits_check.isChecked()
        include_punctuation = self.punctuation_check.isChecked()
        include_latin = self.latin_check.isChecked()
        include_cyrillic = self.cyrillic_check.isChecked()
        return length, include_uppercase, include_lowercase, include_digits, include_punctuation, include_latin, include_cyrillic


class DeleteDialog(QDialog):
    def __init__(self, table_widget, dict):
        super().__init__()
        self.dict = dict
        icon = QIcon('Capy.jpg')
        self.setWindowIcon(icon)
        self.setWindowTitle(self.dict[40])
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

        self.delete_btn = QPushButton(self.dict[5])
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
    window = StartMenu()
    window.show()
    sys.exit(app.exec())
