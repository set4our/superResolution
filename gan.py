import os
import cv2
from loguru import logger
from basicsr.utils import imwrite
from basicsr.utils.video_util import VideoReader, VideoWriter
from basicsr.archs.rrdbnet_arch import RRDBNet
from basicsr.utils.realesrgan_utils import RealESRGANer
import torch
import asyncio
from subtitles import process_file

class GAN:
    def __init__(self, input_path: str, result_root: str = None, apply_subtitles: bool = True, apply_model: bool = True,
                 resolution=(640, 480), progress_callback=None):
        self.input_path: str = input_path
        self.result_root: str = result_root
        self.apply_subtitles: bool = apply_subtitles
        self.apply_model: bool = apply_model
        self.resolution = resolution
        self.progress_callback = progress_callback
        self._device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self._upscale = 2

    def find_files(self):
        video = {"name": None, "audio": None, "fps": None}
        img_list = []

        if self.input_path.endswith(('mp4', 'mov', 'avi', 'MP4', 'MOV', 'AVI')):
            vidr = VideoReader(self.input_path)
            frame = vidr.get_frame()
            while frame is not None:
                img_list.append(frame)
                frame = vidr.get_frame()
            video_name = os.path.basename(self.input_path)[:-4]
            video.update(
                audio=vidr.get_audio(),
                fps=vidr.get_fps(),
                name=video_name
            )
            self.result_root = f"results/{video_name}"
            vidr.close()
        else:
            raise FileNotFoundError(
                "Мне нужна ссылка на видеофайл (mp4, mov, avi, MP4, MOV,))"
            )

        if len(img_list) == 0:
            raise FileNotFoundError(
                "Входное видео не найдено...\n"
                "Мне нужна ссылка на видеофайл (mp4, mov, avi, MP4, MOV,))"
            )

        return video, img_list

    def bg_upsampler(self):
        use_half = False
        if torch.cuda.is_available():
            no_half_gpu_list = ['1650', '1660']
            if True not in [gpu in torch.cuda.get_device_name(0) for gpu in no_half_gpu_list]:
                use_half = True

        model = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=2,
        )

        upsampler = RealESRGANer(
            scale=2,
            model_path="General/models/GAN_model.pth",
            model=model,
            tile=400,
            tile_pad=40,
            pre_pad=0,
            half=use_half
        )

        return upsampler

    async def generate_subtitles(self, video_path):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.process_file_threadsafe, video_path)

    def process_file_threadsafe(self, video_path):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(process_file(video_path))
        loop.close()

    async def run(self):
        video, img_list = self.find_files()
        total_frames = len(img_list)

        for i, img in enumerate(img_list, start=1):
            basename = str(i).zfill(6)
            img_name = f"{video['name']}_{basename}"

            logger.info(f"[{i}/{len(img_list)}] Processing file: {img_name}")

            if self.apply_model:
                bg_img = self.bg_upsampler().enhance(img, outscale=self._upscale)[0]
            else:
                bg_img = img
            bg_img = cv2.resize(bg_img, self.resolution, interpolation=cv2.INTER_AREA)

            if bg_img is not None:
                save_restore_path = os.path.join(self.result_root, video['name'])
                os.makedirs(save_restore_path, exist_ok=True)  # каталог существует или нет
                imwrite(bg_img, os.path.join(save_restore_path, f"{basename}.png"))

            if self.progress_callback:
                self.progress_callback((i / total_frames) * 100)

        if self.apply_subtitles:
            save_restore_path = os.path.join(self.result_root, video['name'])
            await self.generate_subtitles(self.input_path)
            video_frames = [cv2.imread(os.path.join(save_restore_path, frame)) for frame in
                            sorted(os.listdir(save_restore_path)) if frame.endswith('.png')]

            if not os.path.exists(save_restore_path):
                os.makedirs(save_restore_path, exist_ok=True)  # Убедитесь, что каталог существует

            # Определяем объект для записи видео
            fourcc = cv2.VideoWriter_fourcc(*'XVID') # Кодек для MP4
            frame_width, frame_height = video_frames[0].shape[1], video_frames[0].shape[0]
            vidwriter = cv2.VideoWriter(f'{save_restore_path}.mp4', fourcc, video['fps'], (frame_width, frame_height))

            # Запись кадров в видео
            for frame in video_frames:
                vidwriter.write(frame)

            # Выпуск видео для записи
            vidwriter.release()

            logger.info(f"Saved processed video to: {save_restore_path}.mp4")
