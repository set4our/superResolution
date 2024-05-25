import os
from deepgram import Deepgram
import pysrt
from moviepy.config import change_settings
from moviepy.editor import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.io.VideoFileClip import VideoFileClip

change_settings({"IMAGEMAGICK_BINARY": "C:\Program Files\ImageMagick-7.1.1-Q16-HDRI/magick.exe"})

DEEPGRAM_API_KEY = '2baa22c1fd2faf8808f2f472374119fae3d737b3'

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
    output_video_file = 'output_with_subtitles.mp4'

    subtitle_clips = create_subtitle_clips(subtitles, video.size)
    final_video = CompositeVideoClip([video] + subtitle_clips)
    final_video.write_videofile(output_video_file, codec='libx264')
