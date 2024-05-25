import customtkinter as ctk
from tkinter import Text, Scrollbar, messagebox
from email.mime.text import MIMEText
from email.header import Header
import smtplib

class LogWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Logs")
        self.geometry("600x400")
        self.iconbitmap("icon/icon.ico")

        self.text_widget = Text(self)
        self.text_widget.pack(expand=True, fill='both')

        scrollbar = Scrollbar(self.text_widget)
        scrollbar.pack(side='right', fill='y')
        self.text_widget.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.text_widget.yview)

        self.load_logs()

        ctk.CTkButton(self, text="Отправить на почту", command=self.send_email).pack(pady=10)

    def load_logs(self):
        try:
            with open("application.log", "r") as log_file:
                logs = log_file.read()
                self.text_widget.insert('1.0', logs)
        except FileNotFoundError:
            self.text_widget.insert('1.0', "Лог файл не найден")

    def send_email(self):
        recipients_emails = ['klad.ladin@yandex.ru']
        login = 'diplom.test0@yandex.ru'
        password = 'kkcmzyofdnmrcjpu'

        try:
            with open("application.log", "r") as log_file:
                message = log_file.read()

            msg = MIMEText(f'{message}', 'plain', 'utf-8')
            msg['Subject'] = Header('Логи приложения', 'utf-8')
            msg['From'] = login
            msg['To'] = ', '.join(recipients_emails)

            s = smtplib.SMTP('smtp.yandex.ru', 587, timeout=10)
            s.starttls()
            s.login(login, password)
            s.sendmail(msg['From'], recipients_emails, msg.as_string())
            print("Письмо успешно отправлено")
            messagebox.showinfo("Успех", "Письмо успешно отправлено")
        except smtplib.SMTPException as ex:
            print(f"Ошибка при отправке письма: {ex}")
            messagebox.showerror("Ошибка", f"Ошибка при отправке письма: {ex}")
        finally:
            s.quit()
