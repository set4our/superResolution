import os
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from deepgram import Deepgram
import pysrt
from loguru import logger
from tqdm import tqdm
from basicsr.utils import imwrite
from basicsr.utils.video_util import VideoReader, VideoWriter
from basicsr.archs.rrdbnet_arch import RRDBNet
from basicsr.utils.realesrgan_utils import RealESRGANer
import torch
import asyncio
from moviepy.config import change_settings

change_settings({"IMAGEMAGICK_BINARY": "C:\Program Files\ImageMagick-7.1.1-Q16-HDRI/magick.exe"})

DEEPGRAM_API_KEY = '2baa22c1fd2faf8808f2f472374119fae3d737b3'


def apply_sharpening_filter(img):
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return cv2.filter2D(img, -1, kernel)


def increase_contrast(img, alpha=1.5, beta=0):
    return cv2.convertScaleAbs(img, alpha=alpha, beta=beta)


def reduce_noise(img):
    return cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)


def time_to_seconds(time_obj):
    return time_obj.hours * 3600 + time_obj.minutes * 60 + time_obj.seconds + time_obj.milliseconds / 1000


def create_subtitle_clips(subtitles, videosize, fontsize=24, font='Arial', color='yellow'):
    subtitle_clips = []
    for subtitle in subtitles:
        start_time = time_to_seconds(subtitle.start)
        end_time = time_to_seconds(subtitle.end)
        duration = end_time - start_time
        video_width, video_height = videosize
        text_clip = TextClip(subtitle.text, fontsize=fontsize, font=font, color=color, bg_color='black',
                             size=(video_width * 3 / 4, None), method='caption').set_start(start_time).set_duration(
            duration)
        subtitle_x_position = 'center'
        subtitle_y_position = video_height * 4 / 5
        text_position = (subtitle_x_position, subtitle_y_position)
        subtitle_clips.append(text_clip.set_position(text_position))
    return subtitle_clips


async def process_file(file_path):
    PATH_TO_FILE = file_path
    MIMETYPE = 'audio/wav'

    async def init_deepgram():
        dg_client = Deepgram(DEEPGRAM_API_KEY)
        with open(PATH_TO_FILE, 'rb') as audio:
            source = {'buffer': audio, 'mimetype': MIMETYPE}
            options = {"punctuate": True, "model": "nova", "language": "en-US"}
            file_response = await dg_client.transcription.prerecorded(source, options)
            return file_response

    file_response = await init_deepgram()
    subtitle_data = file_response['results']['channels'][0]['alternatives'][0]['words']

    filename = os.path.basename(file_path)
    name, _ = os.path.splitext(filename)
    op_file = name + ".srt"

    def convert_to_srt(data, op_file):
        def format_time(seconds):
            hours, remainder = divmod(seconds, 3600)
            minutes, remainder = divmod(remainder, 60)
            seconds, milliseconds = divmod(remainder, 1)
            return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d},{int(milliseconds * 1000):03d}"

        with open(op_file, 'w') as f:
            for i, entry in enumerate(data, start=1):
                start_time = format_time(entry['start'])
                end_time = format_time(entry['end'])
                subtitle_text = entry['punctuated_word']
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{subtitle_text}\n\n")

    convert_to_srt(subtitle_data, op_file)
    mp4filename = file_path
    srtfilename = op_file

    video = VideoFileClip(mp4filename)
    subtitles = pysrt.open(srtfilename)
    output_video_file = 'output.mp4'

    subtitle_clips = create_subtitle_clips(subtitles, video.size)
    final_video = CompositeVideoClip([video] + subtitle_clips)
    final_video.write_videofile(output_video_file, codec='libx264')


class GAN:
    def __init__(self, input_path: str, result_root: str = None, apply_contrast: bool = True, apply_noise: bool = True,
                 apply_sharpening: bool = True, apply_subtitles: bool = True, apply_model: bool = True):
        self.input_path: str = input_path
        self.result_root: str = result_root
        self.apply_contrast: bool = apply_contrast
        self.apply_noise: bool = apply_noise
        self.apply_sharpening: bool = apply_sharpening
        self.apply_subtitles: bool = apply_subtitles
        self.apply_model: bool = apply_model
        self._device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self._upscale = 2

    def find_files(self):
        img_or_video = False
        video = {"name": None, "audio": None, "fps": None}
        img_list = []

        if self.input_path.endswith(('jpg', 'jpeg', 'png', 'JPG', 'JPEG', 'PNG')):
            img_or_video = False
            img_list.append(self.input_path)
            self.result_root = "results"
        elif self.input_path.endswith(('mp4', 'mov', 'avi', 'MP4', 'MOV', 'AVI')):
            vidr = VideoReader(self.input_path)
            frame = vidr.get_frame()
            while frame is not None:
                img_list.append(frame)
                frame = vidr.get_frame()
            video_name = os.path.basename(self.input_path)[:-4]
            img_or_video = True
            video.update(
                audio=vidr.get_audio(),
                fps=vidr.get_fps(),
                name=video_name
            )
            self.result_root = f"results/{video_name}"
            vidr.close()
        else:
            raise FileNotFoundError(
                "Я не понял, какой файл загружать...\n"
                "Мне нужна ссылка на фото (jpg, jpeg, png, JPG, JPEG, PNG),"
                " или на видео (mp4, mov, avi, MP4, MOV, AVI)"
            )

        if len(img_list) == 0:
            raise FileNotFoundError(
                "Входное изображение/видео не найдено...\n"
                "Мне нужна ссылка на фото (jpg, jpeg, png, JPG, JPEG, PNG),"
                " или на видео (mp4, mov, avi, MP4, MOV, AVI)"
            )

        return img_or_video, video, img_list

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
        await process_file(video_path)

    async def run(self):
        img_or_video, video, img_list = self.find_files()

        for i, img_path in enumerate(img_list, start=1):
            if not img_or_video:
                img_name = os.path.basename(img_path)
                basename, ext = os.path.splitext(img_name)
                img = cv2.imread(img_path, cv2.IMREAD_COLOR)
            else:
                basename = str(i).zfill(6)
                img_name = f"{video['name']}_{basename}"
                img = img_path

            logger.info(f"[{i}/{len(img_list)}] Обработка файла: {img_name}")

            if self.apply_sharpening:
                sharpened_img = apply_sharpening_filter(img)
            else:
                sharpened_img = img

            if self.apply_contrast:
                contrast_img = increase_contrast(sharpened_img)
            else:
                contrast_img = sharpened_img

            if self.apply_noise:
                denoised_img = reduce_noise(contrast_img)
            else:
                denoised_img = contrast_img

            if self.apply_model:
                bg_img = self.bg_upsampler().enhance(denoised_img, outscale=self._upscale)[0]
            else:
                bg_img = denoised_img
            bg_img = cv2.resize(bg_img, (640, 480), interpolation=cv2.INTER_AREA)

            if bg_img is not None:
                if img_or_video:
                    save_restore_path = os.path.join(self.result_root, video['name'])
                    if not os.path.exists(save_restore_path):
                        os.makedirs(save_restore_path)
                    imwrite(bg_img, os.path.join(save_restore_path, f"{basename}.png"))
                else:
                    if not os.path.exists(self.result_root):
                        os.makedirs(self.result_root)
                    save_restore_path = os.path.join(self.result_root, f"{basename}.png")
                    imwrite(bg_img, save_restore_path)

        if self.apply_subtitles and img_or_video:
            save_restore_path = os.path.join(self.result_root, video['name'])
            await self.generate_subtitles(self.input_path)
            video_frames = [cv2.imread(os.path.join(save_restore_path, frame)) for frame in
                            sorted(os.listdir(save_restore_path)) if frame.endswith('.png')]

            vidwriter = VideoWriter(f'{save_restore_path}.mp4', video_frames[0].shape[0], video_frames[0].shape[1],
                                    video['fps'], video['audio'])
            for frame in video_frames:
                vidwriter.write_frame(frame)
            vidwriter.close()


async def multi_files(path, apply_contrast, apply_noise, apply_sharpening, apply_subtitles, apply_model):
    process = GAN(path, apply_contrast=apply_contrast, apply_noise=apply_noise, apply_sharpening=apply_sharpening,
                  apply_subtitles=apply_subtitles, apply_model=apply_model)
    await process.run()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GAN video processing")
    parser.add_argument("--path", type=str, required=True, help="Path to the input file (image or video)")
    parser.add_argument("--contrast", action="store_true", help="Apply contrast enhancement")
    parser.add_argument("--noise", action="store_true", help="Apply noise reduction")
    parser.add_argument("--sharpen", action="store_true", help="Apply sharpening")
    parser.add_argument("--subtitles", action="store_true", help="Generate and apply subtitles")
    parser.add_argument("--model", action="store_true", help="Apply GAN model enhancement")

    args = parser.parse_args()

    asyncio.run(multi_files(args.path, args.contrast, args.noise, args.sharpen, args.subtitles, args.model))

