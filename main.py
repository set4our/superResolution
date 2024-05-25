import os
import time

import customtkinter as ctk
from tkinter import filedialog, messagebox, Entry
from tkinter.ttk import Progressbar
import asyncio
from threading import Thread

import cv2
from moviepy.editor import VideoFileClip, ImageSequenceClip

from basicsr.models.base_model import logger
from system_info_window import SystemInfoWindow
from log_window import LogWindow
from video_editor_window import VideoEditorWindow

from gan import GAN

class Application(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Улучшение видео и генерация субтитров")
        self.geometry("400x550")
        self.iconbitmap("icon/icon.ico")

        self.video_path = ctk.StringVar()
        self.subtitles = ctk.BooleanVar()
        self.model = ctk.BooleanVar()
        self.resolution = ctk.StringVar(value="854x480")

        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Выберите видеофайл:").pack(pady=10)
        Entry(self, textvariable=self.video_path, width=50).pack(pady=5)
        ctk.CTkButton(self, text="Обзор", command=self.browse_file).pack(pady=5)

        ctk.CTkCheckBox(self, text="Создать субтитры", variable=self.subtitles,
                        command=self.check_processing_options).pack(pady=5)
        ctk.CTkCheckBox(self, text="Улучшить качество видео", variable=self.model,
                        command=self.check_processing_options).pack(pady=5)

        ctk.CTkLabel(self, text="Выберите разрешение видео:").pack(pady=10)
        self.resolution_option = ctk.CTkOptionMenu(self, variable=self.resolution, values=["854x480", "1280x720", "1920x1080"])
        self.resolution_option.configure(state=ctk.DISABLED)
        self.resolution_option.pack(pady=5)

        self.progress = Progressbar(self, orient=ctk.HORIZONTAL, length=300, mode='determinate')
        self.progress.pack(pady=20)

        self.process_button = ctk.CTkButton(self, text="Обработать", command=self.process_video, state=ctk.DISABLED)
        self.process_button.pack(pady=10)

        ctk.CTkButton(self, text="Информация об оборудовании", command=self.show_system_info).pack(pady=10)
        ctk.CTkButton(self, text="Logs", command=self.show_logs).pack(pady=10)
        ctk.CTkButton(self, text="Видеоредактор", command=self.show_video_editor).pack(pady=10)

    def check_processing_options(self):
        if self.subtitles.get() or self.model.get():
            self.process_button.configure(state=ctk.NORMAL)
        else:
            self.process_button.configure(state=ctk.DISABLED)

        if self.subtitles.get() and self.model.get():
            messagebox.showerror("Ошибка", "Пожалуйста, выберите только один параметр обработки")
            self.process_button.configure(state=ctk.DISABLED)

        self.toggle_resolution_option()

    def toggle_resolution_option(self):
        if self.model.get():
            self.resolution_option.configure(state=ctk.NORMAL)
        else:
            self.resolution_option.configure(state=ctk.DISABLED)

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Видеофайлы", "*.mp4 *.mov *.avi")])
        if file_path:
            self.video_path.set(file_path)

    def process_video(self):
        if not self.video_path.get():
            messagebox.showerror("Ошибка", "Пожалуйста, выберите видеофайл")
            return

        if self.subtitles.get() and self.model.get():
            messagebox.showerror("Ошибка", "Пожалуйста, выберите только один параметр обработки")
            return

        resolution = tuple(map(int, self.resolution.get().split('x')))
        result_root = os.path.join('results', os.path.splitext(os.path.basename(self.video_path.get()))[0])

        thread = Thread(target=self.run_processing,
                        args=(self.video_path.get(), result_root, self.subtitles.get(), self.model.get(), resolution))
        thread.start()

    def run_processing(self, input_path, result_root, apply_subtitles, apply_model, resolution):
        self.progress.start()
        try:
            async def process():
                gan = GAN(input_path, result_root, apply_subtitles=apply_subtitles, apply_model=apply_model,
                          resolution=resolution, progress_callback=self.update_progress)
                await gan.run()
                if apply_subtitles:
                    self.process_with_subtitles(result_root)
                else:
                    video_name = os.path.basename(input_path)
                    output_video = os.path.join(result_root, f'{os.path.splitext(video_name)[0]}.mp4')

                    # Создаем видео из кадров перед открытием окна сохранения файла
                    self.create_video_from_frames(result_root, video_name, input_path)
                    # Открываем окно сохранения файла
                    self.save_output(output_video)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process())
            loop.close()

            self.progress.stop()
            messagebox.showinfo("Информация", "Обработка завершена")
        except Exception as e:
            logger.error(f"Ошибка обработки видео: {e}")
            messagebox.showerror("Ошибка", f"Произошла ошибка при обработке видео: {e}")
            self.progress.stop()

    def create_video_from_frames(self, result_dir, video_name, input_path):
        result_dirs = [d for d in os.listdir('results') if os.path.isdir(os.path.join('results', d))]
        latest_result_dir = max(result_dirs, key=lambda d: os.path.getmtime(os.path.join('results', d)))
        latest_result_dir = os.path.join(result_dir, latest_result_dir)
        frames_path = os.path.join(latest_result_dir)

        video_frames = [os.path.join(frames_path, frame) for frame in sorted(os.listdir(frames_path)) if
                        frame.endswith('.png')]
        if video_frames:
            intermediate_video_path = os.path.join(result_dir, f'{video_name}')
            original_video = VideoFileClip(input_path)
            fps = original_video.fps

            # Создаем видео из последовательности кадров с помощью moviepy
            clip = ImageSequenceClip(video_frames, fps=fps)
            clip.write_videofile(intermediate_video_path, codec='libx264', audio=False)

            # Извлечение аудио из оригинального видео с помощью moviepy
            audio_clip = original_video.audio

            # Объединение аудио и видео с помощью moviepy
            final_clip = clip.set_audio(audio_clip)
            final_output_path = os.path.join(result_dir, f'{video_name}')
            final_clip.write_videofile(final_output_path, codec='libx264', audio_codec='aac')

            # Закрытие клипов после завершения работы
            clip.close()
            audio_clip.close()
            original_video.close()
            final_clip.close()

            # Проверяем длительность исходного и финального видео
            final_video = VideoFileClip(final_output_path)
            if abs(original_video.duration - final_video.duration) > 1:
                messagebox.showwarning("Предупреждение", "Длительность исходного и финального видео не совпадает")

            # Закрытие финального клипа после завершения проверки
            final_video.close()

        else:
            messagebox.showerror("Ошибка", "Не удалось найти кадры для создания видео")
    def save_output(self, output_video):
        if os.path.exists(output_video):
            save_path = filedialog.asksaveasfilename(defaultextension=".mp4",
                                                     filetypes=[("Видеофайлы", "*.mp4;*.avi;*.mov")],
                                                     initialdir=os.path.dirname(output_video))
            if save_path:
                # Попытка задержки перед перемещением файла
                time.sleep(2)
                try:
                    os.replace(output_video, save_path)
                except PermissionError as e:
                    messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")
        else:
            messagebox.showerror("Ошибка", f"Файл {output_video} не существует")

    def process_with_subtitles(self, result_root):
        # Задаем корневую папку проекта
        project_root = os.path.dirname(os.path.abspath(__file__))
        output_video = os.path.join(project_root, 'output_with_subtitles.mp4')

        if os.path.exists(output_video):
            save_path = filedialog.asksaveasfilename(defaultextension=".mp4",
                                                     filetypes=[("Видеофайлы", "*.mp4;*.avi;*.mov")],
                                                     initialdir=os.path.dirname(output_video))
            if save_path:
                os.replace(output_video, save_path)
        else:
            messagebox.showerror("Ошибка", f"Файл {output_video} не существует")

    def update_progress(self, value):
        self.progress['value'] = value

    def show_system_info(self):
        system_info_window = SystemInfoWindow(self)
        system_info_window.grab_set()

    def show_logs(self):
        log_window = LogWindow(self)
        log_window.grab_set()

    def show_video_editor(self):
        video_editor_window = VideoEditorWindow(self)
        video_editor_window.grab_set()

if __name__ == "__main__":
        ctk.set_appearance_mode("light")
        app = Application()
        app.mainloop()

