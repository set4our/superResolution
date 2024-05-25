import os
from customtkinter import *
from tkinter import filedialog, messagebox, Tk, Toplevel, Entry
from moviepy.editor import VideoFileClip


class VideoEditorWindow(Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Видеоредактор")
        self.iconbitmap("icon/icon.ico")

        self.video_path = StringVar()
        self.video_duration = StringVar()
        self.start_time = StringVar()
        self.end_time = StringVar()

        self.create_widgets()

    def create_widgets(self):
        frame1 = CTkFrame(self)
        frame1.pack()

        CTkLabel(frame1, text="Выберите видеофайл:").pack(side=LEFT, padx=10, pady=10)
        self.video_entry = Entry(frame1, textvariable=self.video_path, width=50)
        self.video_entry.pack(side=LEFT, padx=10, pady=10)
        CTkButton(frame1, text="Обзор", command=self.open_video_file).pack(side=LEFT, padx=10, pady=10)

        CTkLabel(self, text="Продолжительность видео:").pack(side=TOP, padx=10, pady=10)
        CTkLabel(self, textvariable=self.video_duration).pack(side=TOP, padx=10, pady=10)

        frame2 = CTkFrame(self)
        frame2.pack()

        CTkLabel(frame2, text="Время начала обрезки (сек):").pack(side=LEFT, padx=10, pady=5)
        Entry(frame2, textvariable=self.start_time, width=10).pack(side=LEFT, padx=5, pady=5)

        CTkLabel(frame2, text="Время окончания обрезки (сек):").pack(side=LEFT, padx=10, pady=5)
        Entry(frame2, textvariable=self.end_time, width=10).pack(side=LEFT, padx=5, pady=5)

        CTkButton(self, text="Воспроизвести", command=self.play_video).pack(side=TOP, padx=10, pady=10)
        CTkButton(self, text="Сохранить", command=self.save_video).pack(side=TOP, padx=10, pady=10)

    def open_video_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Видеофайлы", "*.mp4;*.avi;*.mov")])
        if file_path:
            self.video_path.set(file_path)
            video_clip = VideoFileClip(file_path)
            self.video_duration.set(f"{video_clip.duration:.2f} сек")
            video_clip.close()

    def play_video(self):
        if not self.video_path.get():
            messagebox.showerror("Ошибка", "Выберите видео файл.")
            return

        os.system(f'start {self.video_path.get()}')

    def save_video(self):
        if not self.video_path.get():
            messagebox.showerror("Ошибка", "Выберите видео файл.")
            return

        output_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("Видеофайлы", "*.mp4;*.avi;*.mov")])
        if output_path:
            start_time = float(self.start_time.get()) if self.start_time.get() else 0.0
            end_time = float(self.end_time.get()) if self.end_time.get() else None

            video_clip = VideoFileClip(self.video_path.get()).subclip(start_time, end_time)
            video_clip.write_videofile(output_path)
            video_clip.close()
            messagebox.showinfo("Информация", "Видео успешно сохранено.")



def main():
    root = Tk()
    editor = VideoEditorWindow(root)
    editor.grab_set()  # Ensure the new window is modal
    root.mainloop()


if __name__ == "__main__":
    main()
