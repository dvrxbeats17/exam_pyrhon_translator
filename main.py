import hashlib
import sqlite3
from googletrans import Translator, LANGUAGES


class UserDB:
    def __init__(self, user_db_name, translation_db_name):
        self.user_conn = sqlite3.connect(user_db_name)
        self.user_cursor = self.user_conn.cursor()
        self.translation_conn = sqlite3.connect(translation_db_name)
        self.translation_cursor = self.translation_conn.cursor()
        self.create_table()

    def create_table(self):
        self.user_cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                                    username TEXT PRIMARY KEY,
                                    password TEXT)''')
        self.user_conn.commit()

        self.translation_cursor.execute('''CREATE TABLE IF NOT EXISTS translations (
                                            user_id TEXT,
                                            input_text TEXT,
                                            translated_text TEXT,
                                            input_lang TEXT,
                                            output_lang TEXT,
                                            translation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                            FOREIGN KEY(user_id) REFERENCES users(username)
                                        )''')
        self.translation_conn.commit()

    def register_user(self, username: str, password: str) -> None:
        hashed_password = hashlib.sha512(password.encode()).hexdigest()
        self.user_cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        self.user_conn.commit()

    def login_user(self, username: str, password: str) -> bool:
        hashed_password = hashlib.sha512(password.encode()).hexdigest()
        self.user_cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password))
        return self.user_cursor.fetchone() is not None

    def view_translation_history(self, username: str):
        self.translation_cursor.execute("SELECT * FROM translations WHERE user_id=?", (username,))
        history = self.translation_cursor.fetchall()
        if history:
            print("\nИстория переводов:")
            for row in history:
                print(f"ID: {row[5]}, Введенный текст: {row[1]}, Переведенный текст: {row[2]}, Введенный язык: {row[3]}, Язык вывода: {row[4]}")
        else:
            print("История переводов пуста.")

    def close(self):
        self.user_conn.close()
        self.translation_conn.close()


def print_supported_languages():
    print("\nПоддерживаемые языки:")
    for code, lang in LANGUAGES.items():
        print(f"{code}: {lang}")


def translate_text(user_authenticated: bool, username: str, db: UserDB):
    if not user_authenticated:
        print("Необходимо войти в аккаунт или зарегистрироваться.")
        return

    translator = Translator()
    source_lang = input("Введите язык: ")
    target_lang = input("Введите язык: ")

    while True:
        text = input("Введите текст: ")

        if text.lower() == 'exit':
            break

        translated_text = translator.translate(text, src=source_lang, dest=target_lang)
        print("Переведенный текст:", translated_text.text)

        db.translation_cursor.execute("INSERT INTO translations (user_id, input_text, translated_text, input_lang, output_lang) VALUES (?, ?, ?, ?, ?)", (username, text, translated_text.text, source_lang, target_lang))
        db.translation_conn.commit()

        change_lang = input("Хотите поменять языки? (yes/no/new): ")
        if change_lang.lower() == 'yes':
            source_lang, target_lang = target_lang, source_lang
        elif change_lang.lower() == 'new':
            source_lang = input("Введите новый язык: ")
            target_lang = input("Введите новый язык: ")


def main():
    db = UserDB('users.db', 'translations.db')
    print_supported_languages()
    user_authenticated = False

    while True:
        print("1. Регистрация")
        print("2. Логин")
        print("3. Перевод текста")
        print("4. Просмотр истории переводов")
        print("5. Выход")
        choice = input("Выберите что сделать: ")

        if choice == '1':
            username = input("Введите ник: ")
            password = input("Введите пароль: ")
            db.register_user(username, password)
            print("Успешная регистрация!")
        elif choice == '2':
            username = input("Введите ник: ")
            password = input("Введите пароль: ")
            if db.login_user(username, password):
                print("Успешная авторизация!")
                user_authenticated = True
            else:
                print("Неправильный логин или пароль!")
        elif choice == '3':
            translate_text(user_authenticated, username, db)
        elif choice == '4':
            if user_authenticated:
                db.view_translation_history(username)
            else:
                print("Необходимо войти в аккаунт.")
        elif choice == '5':
            db.close()
            print("До свидания!")
            break
        else:
            print("Такого пока нет, попробуйте снова.")


main()
