import os
from tkinter import messagebox, Toplevel

import customtkinter as ctk
from email.header import Header
from email.mime.text import MIMEText
import psutil
import smtplib
import GPUtil
import platform

import tkinter as tk


class SystemInfoWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Информация о конфигурации системы")
        self.geometry("700x600")
        self.iconbitmap("icon/icon.ico")

        self.create_widgets()
        self.display_system_info()

    def create_widgets(self):
        self.text_display = ctk.CTkTextbox(self)
        self.text_display.pack(expand=True, fill='both', padx=10, pady=10)

        self.refresh_button = ctk.CTkButton(self, text="Обновить", command=self.display_system_info)
        self.refresh_button.pack(pady=10)

        self.send_email_button = ctk.CTkButton(self, text="Отправить на почту", command=self.send_email)
        self.send_email_button.pack(pady=10)

    def display_system_info(self):
        self.text_display.configure(state='normal')
        self.text_display.delete(1.0, ctk.END)

        system_info_text = self.get_system_info_text()

        self.text_display.insert(ctk.END, system_info_text)
        self.text_display.configure(state='disabled')

    def get_system_info_text(self):
        cpu_info = self.get_cpu_info()
        memory_info = self.get_memory_info()
        disk_info = self.get_disk_info()
        network_info = self.get_network_info()
        gpu_info = self.get_gpu_info()

        system_info_text = ""
        system_info_text += "Информация о процессоре:\n" + cpu_info + "\n"
        system_info_text += "Информация о памяти:\n" + memory_info + "\n"
        system_info_text += "Информация о дисках:\n" + disk_info + "\n"
        system_info_text += "Информация о сети:\n" + network_info + "\n"
        system_info_text += "Информация о видеокарте:\n" + gpu_info + "\n"

        return system_info_text

    def get_cpu_info(self):
        cpu_info = f"Процессор: {platform.processor()}\n"
        cpu_info += f"Физические ядра: {psutil.cpu_count(logical=False)}\n"
        cpu_info += f"Всего ядер: {psutil.cpu_count(logical=True)}\n"
        cpu_freq = psutil.cpu_freq()
        cpu_info += f"Максимальная частота: {cpu_freq.max:.2f} МГц\n"
        cpu_info += f"Минимальная частота: {cpu_freq.min:.2f} МГц\n"
        cpu_info += f"Текущая частота: {cpu_freq.current:.2f} МГц\n"
        cpu_info += "Использование CPU по ядрам:\n"
        for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
            cpu_info += f"Ядро {i}: {percentage}%\n"
        cpu_info += f"Общее использование CPU: {psutil.cpu_percent()}%\n"
        return cpu_info

    def get_memory_info(self):
        svmem = psutil.virtual_memory()
        memory_info = f"Всего: {self.get_size(svmem.total)}\n"
        memory_info += f"Доступно: {self.get_size(svmem.available)}\n"
        memory_info += f"Используется: {self.get_size(svmem.used)}\n"
        memory_info += f"Процент: {svmem.percent}%\n"
        return memory_info

    def get_disk_info(self):
        partitions = psutil.disk_partitions()
        disk_info = ""
        for partition in partitions:
            disk_info += f"=== Устройство: {partition.device} ===\n"
            disk_info += f"  Точка монтирования: {partition.mountpoint}\n"
            disk_info += f"  Тип файловой системы: {partition.fstype}\n"
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
            except PermissionError:
                continue
            disk_info += f"  Общий размер: {self.get_size(partition_usage.total)}\n"
            disk_info += f"  Используется: {self.get_size(partition_usage.used)}\n"
            disk_info += f"  Свободно: {self.get_size(partition_usage.free)}\n"
            disk_info += f"  Процент: {partition_usage.percent}%\n"
        return disk_info

    def get_network_info(self):
        net_io = psutil.net_io_counters()
        network_info = f"Всего отправлено байт: {self.get_size(net_io.bytes_sent)}\n"
        network_info += f"Всего получено байт: {self.get_size(net_io.bytes_recv)}\n"
        return network_info

    def get_gpu_info(self):
        gpus = GPUtil.getGPUs()
        gpu_info = ""
        for gpu in gpus:
            gpu_info += f"ID: {gpu.id}, Имя: {gpu.name}\n"
            gpu_info += f"  Загрузка: {gpu.load * 100}%\n"
            gpu_info += f"  Общая память: {self.get_size(gpu.memoryTotal)}\n"
            gpu_info += f"  Используемая память: {self.get_size(gpu.memoryUsed)}\n"
            gpu_info += f"  Свободная память: {self.get_size(gpu.memoryFree)}\n"
            gpu_info += f"  Температура: {gpu.temperature} °C\n"
        return gpu_info if gpu_info else "Видеокарта не найдена."

    def get_size(self, bytes, suffix="Б"):
        factor = 1024
        for unit in ["", "К", "М", "Г", "Т", "П"]:
            if bytes < factor:
                return f"{bytes:.2f}{unit}{suffix}"
            bytes /= factor

    def send_email(self):
        # Получение системной информации для отправки
        message = self.get_system_info_text()

        # Адреса электронной почты получателей
        recipients_emails = ['klad.ladin@yandex.ru']

        # Логин и пароль
        login = 'diplom.test0@yandex.ru'  # логин (адрес электронной почты Yandex)
        password = 'kkcmzyofdnmrcjpu'

        # Создание сообщения
        msg = MIMEText(f'{message}', 'plain', 'utf-8')
        msg['Subject'] = Header('Информация о конфигурации системы', 'utf-8')
        msg['From'] = login
        msg['To'] = ', '.join(recipients_emails)

        try:
            # Настройка и отправка письма
            s = smtplib.SMTP('smtp.yandex.ru', 587, timeout=10)
            s.starttls()
            s.login(login, password)
            s.sendmail(msg['From'], recipients_emails, msg.as_string())
            print("Письмо успешно отправлено")
            messagebox.showinfo("Успех", "Письмо успешно отправлено")
        except smtplib.SMTPException as ex:
            print(f"Ошибка при отправке письма: {ex}")
        finally:
            s.quit()


# if __name__ == "__main__":
#     ctk.set_appearance_mode("light")  # Можно сменить на "light" для светлой темы
#     ctk.set_default_color_theme("blue")  # Можно сменить на "green" или "dark-blue"
#     root = ctk.CTk()
#     app = SystemInfoWindow(root)
#     root.mainloop()
