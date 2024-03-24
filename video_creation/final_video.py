import multiprocessing
import os
import re
from os.path import exists  # Needs to be imported specifically
from typing import Final
from typing import Tuple, Any, Dict

import ffmpeg
import translators
from PIL import Image
from rich.console import Console
from rich.progress import track

from utils.cleanup import cleanup
from utils.console import print_step, print_substep
from utils.thumbnail import create_thumbnail
from utils.videos import save_data
from utils import settings

import tempfile
import threading
import time
import random
import string

console = Console()


class ProgressFfmpeg(threading.Thread):
    def __init__(self, vid_duration_seconds, progress_update_callback):
        threading.Thread.__init__(self, name="ProgressFfmpeg")
        self.stop_event = threading.Event()
        self.output_file = tempfile.NamedTemporaryFile(mode="w+", delete=False)
        self.vid_duration_seconds = vid_duration_seconds
        self.progress_update_callback = progress_update_callback

    def run(self):
        while not self.stop_event.is_set():
            latest_progress = self.get_latest_ms_progress()
            if latest_progress is not None:
                completed_percent = latest_progress / self.vid_duration_seconds
                self.progress_update_callback(completed_percent)
            time.sleep(1)

    def get_latest_ms_progress(self):
        lines = self.output_file.readlines()
        # print("lines")
        # print(self.output_file.name)

        if lines:
            for line in lines:
                if "out_time_ms" in line:
                    out_time_ms = line.split("=")[1].strip()
                    if out_time_ms != "N/A":
                        return int(out_time_ms) / 1000000.0
                    else:
                        return 0
        return None

    def stop(self):
        self.stop_event.set()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args, **kwargs):
        self.stop()


def wrap_text(text, fontSize, max_width):
    lines = []
    line = ''
    for word in text.split():
        if fontSize <= max_width:
            line += (word + ' ')
        else:
            lines.append(line)
            line = word + ' '
    lines.append(line)
    return '\n'.join(lines)


def name_normalize(name: str) -> str:
    name = re.sub(r'[?\\"%*:|<>]', "", name)
    name = re.sub(r"( [w,W]\s?\/\s?[o,O,0])", r" without", name)
    name = re.sub(r"( [w,W]\s?\/)", r" with", name)
    name = re.sub(r"(\d+)\s?\/\s?(\d+)", r"\1 of \2", name)
    name = re.sub(r"(\w+)\s?\/\s?(\w+)", r"\1 or \2", name)
    name = re.sub(r"\/", r"", name)

    lang = settings.config["reddit"]["thread"]["post_lang"]
    if lang:
        print_substep("Translating filename...")
        translated_name = translators.google(name, to_language=lang)
        return translated_name
    else:
        return name


def prepare_background(reddit_id: str, W: int, H: int) -> str:
    output_path = f"assets/temp/{reddit_id}/background_noaudio.mp4"
    output = (
        ffmpeg.input(f"assets/temp/{reddit_id}/background.mp4")
        .filter("crop", f"ih*({W}/{H})", "ih")
        .output(
            output_path,
            an=None,
            **{
                # 原来的配置
                # "c:v": "h264",
                # "b:v": "20M",
                # "b:a": "192k",
                "c:v": "libx264",  # 更改为libx264以使用更高质量的视频编码器
                "b:v": "20M",      # 增加输出视频的比特率
                "b:a": "192k",
                "threads": multiprocessing.cpu_count(),
            },
        )
        .overwrite_output()
    )
    try:
        output.run(quiet=True)
    except ffmpeg.Error as e:
        print(e.stderr.decode("utf8"))
        exit(1)
    return output_path


def merge_background_audio(audio: ffmpeg, reddit_id: str):
    """Gather an audio and merge with assets/backgrounds/background.mp3
    Args:
        audio (ffmpeg): The TTS final audio but without background.
        reddit_id (str): The ID of subreddit
    """
    background_audio_volume = settings.config["settings"]["background"][
        "background_audio_volume"
    ]
    if background_audio_volume == 0:
        return audio  # Return the original audio
    else:
        # sets volume to config
        bg_audio = ffmpeg.input(f"assets/temp/{reddit_id}/background.mp3").filter(
            "volume",
            background_audio_volume,
        )
        # Merges audio and background_audio
        merged_audio = ffmpeg.filter([audio, bg_audio], "amix", duration="longest")
        return merged_audio  # Return merged audio

# 定义一个函数来生成随机中文文本
def generate_random_chinese(length):
    result = ''
    for _ in range(length):
        result += random.choice(string.ascii_letters + string.digits + '，。！？：；、')
    return result


def after_final_video(
    reddit_obj: dict,
    background_config: Dict[str, Tuple],
):
    subreddit = settings.config["reddit"]["thread"]["subreddit"]
    title = re.sub(r"[^\w\s-]", "", reddit_obj["thread_title"])
    idx = re.sub(r"[^\w\s-]", "", reddit_obj["thread_id"])
    title_thumb = reddit_obj["thread_title"]

    filename = f"{name_normalize(title)[:251]}"

    defaultPath = f"results/{subreddit}"
    path = defaultPath + f"/{filename}"
    original_file = (
        path[:251] + ".mp4"
    )
    input_file = (
        path[:251] + "_music.mp4"
    )  # Prevent a error by limiting the path length, do not change this.
    # 使用 FFmpeg 调整视频分辨率为 1080x1920，并保持宽高比不变


    # 随机选择一个音频文件
    music_folder = "music"
    music_files = [os.path.join(music_folder, file) for file in os.listdir(music_folder) if file.lower().endswith(".mp3")]
    selected_music = random.choice(music_files)

    # 获取视频文件的持续时间
    probe = ffmpeg.probe(original_file)
    video_info = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
    duration = float(video_info["duration"])

    # 定义 FFmpeg 命令
    input_stream = ffmpeg.input(original_file)
    audio_stream = ffmpeg.input(selected_music, t=duration)  # 使用音频文件的持续时间与视频流匹配
    output_stream = ffmpeg.output(input_stream.video, audio_stream.audio, input_file)

    # 设置覆盖选项
    output_stream = output_stream.overwrite_output()

    # 运行 FFmpeg 命令
    ffmpeg.run(output_stream)


    output_file = (
        path[:251] + "_output.mp4"
    )




    # 使用ffmpeg.probe获取视频文件信息
    probe = ffmpeg.probe(input_file)

    # 从probe结果中提取视频流的宽度和高度
    video_info = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video')
    width = int(video_info['width'])
    height = int(video_info['height'])

    print("视频宽度:", width)
    print("视频高度:", height)

    converted_width = height
    converted_height = width

    ffmpeg.input(
        input_file
    ).output(
        output_file,
        vf=f"split[a][b];[a]scale={converted_width}:{converted_height},boxblur=20:5[1];[b]scale={converted_width}:ih*{converted_width}/iw[2];[1][2]overlay=4:(H-h)/2",
        vcodec="libx264",
        acodec="aac",
        crf=18,
        preset="veryfast",
        aspect="9:16",
        f="mp4"
    ).run(overwrite_output=True)

    # # ffmpeg.input(input_file).output(output_file, vf="scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,boxblur=10", vcodec="libx264", acodec="aac").run(overwrite_output=True)


def make_final_video(
    number_of_clips: int,
    length: int,
    reddit_obj: dict,
    background_config: Dict[str, Tuple],
):
    """Gathers audio clips, gathers all screenshots, stitches them together and saves the final video to assets/temp
    Args:
        number_of_clips (int): Index to end at when going through the screenshots'
        length (int): Length of the video
        reddit_obj (dict): The reddit object that contains the posts to read.
        background_config (Tuple[str, str, str, Any]): The background config to use.
    """
    # settings values
    W: Final[int] = int(settings.config["settings"]["resolution_w"])
    H: Final[int] = int(settings.config["settings"]["resolution_h"])

    opacity = settings.config["settings"]["opacity"]

    reddit_id = re.sub(r"[^\w\s-]", "", reddit_obj["thread_id"])

    allowOnlyTTSFolder: bool = (
        settings.config["settings"]["background"]["enable_extra_audio"]
        and settings.config["settings"]["background"]["background_audio_volume"] != 0
    )

    print_step("Creating the final video 🎥")

    background_clip = ffmpeg.input(prepare_background(reddit_id, W=W, H=H))

    # Gather all audio clips
    audio_clips = list()
    if number_of_clips == 0 and settings.config["settings"]["storymode"] == "false":
        print(
            "No audio clips to gather. Please use a different TTS or post."
        )  # This is to fix the TypeError: unsupported operand type(s) for +: 'int' and 'NoneType'
        exit()
    if settings.config["settings"]["storymode"]:
        if settings.config["settings"]["storymodemethod"] == 0:
            audio_clips = [ffmpeg.input(f"assets/temp/{reddit_id}/mp3/title.mp3")]
            audio_clips.insert(
                1, ffmpeg.input(f"assets/temp/{reddit_id}/mp3/postaudio.mp3")
            )
        elif settings.config["settings"]["storymodemethod"] == 1:
            audio_clips = [
                ffmpeg.input(f"assets/temp/{reddit_id}/mp3/postaudio-{i}.mp3")
                for i in track(
                    range(number_of_clips + 1), "Collecting the audio files..."
                )
            ]
            audio_clips.insert(
                0, ffmpeg.input(f"assets/temp/{reddit_id}/mp3/title.mp3")
            )

    else:
        audio_clips = [
            ffmpeg.input(f"assets/temp/{reddit_id}/mp3/{i}.mp3")
            for i in range(number_of_clips)
        ]
        audio_clips.insert(0, ffmpeg.input(f"assets/temp/{reddit_id}/mp3/title.mp3"))

        audio_clips_durations = [
            float(
                ffmpeg.probe(f"assets/temp/{reddit_id}/mp3/{i}.mp3")["format"][
                    "duration"
                ]
            )
            for i in range(number_of_clips)
        ]
        audio_clips_durations.insert(
            0,
            float(
                ffmpeg.probe(f"assets/temp/{reddit_id}/mp3/title.mp3")["format"][
                    "duration"
                ]
            ),
        )
    audio_concat = ffmpeg.concat(*audio_clips, a=1, v=0)
    ffmpeg.output(
        audio_concat, f"assets/temp/{reddit_id}/audio.mp3", **{"b:a": "192k"}
    ).overwrite_output().run(quiet=True)

    console.log(f"[bold green] Video Will Be: {length} Seconds Long")

    # bigrayray 这里原来是45，图片总是超出去，不知道为啥，所以换成25先
    # screenshot_width = int((W * 45) // 100) 
    print("Width")
    print(W)
    screenshot_width = int((W * 99) // 100)


    audio = ffmpeg.input(f"assets/temp/{reddit_id}/audio.mp3")
    final_audio = merge_background_audio(audio, reddit_id)

    image_clips = list()

    image_clips.insert(
        0,
        ffmpeg.input(f"assets/temp/{reddit_id}/png/title.png")["v"].filter(
            "scale", screenshot_width, -1
        ),
    )

    current_time = 0
    if settings.config["settings"]["storymode"]:
        audio_clips_durations = [
            float(
                ffmpeg.probe(f"assets/temp/{reddit_id}/mp3/postaudio-{i}.mp3")[
                    "format"
                ]["duration"]
            )
            for i in range(number_of_clips)
        ]
        audio_clips_durations.insert(
            0,
            float(
                ffmpeg.probe(f"assets/temp/{reddit_id}/mp3/title.mp3")["format"][
                    "duration"
                ]
            ),
        )
        if settings.config["settings"]["storymodemethod"] == 0:
            image_clips.insert(
                1,
                ffmpeg.input(f"assets/temp/{reddit_id}/png/story_content.png").filter(
                    "scale", screenshot_width, -1
                ),
            )
            background_clip = background_clip.overlay(
                image_clips[1],
                enable=f"between(t,{current_time},{current_time + audio_clips_durations[1]})",
                x="(main_w-overlay_w)/2",
                y="(main_h-overlay_h)/2",
            )
            current_time += audio_clips_durations[1]
        elif settings.config["settings"]["storymodemethod"] == 1:
            for i in track(
                range(0, number_of_clips + 1), "Collecting the image files..."
            ):
                image_clips.append(
                    ffmpeg.input(f"assets/temp/{reddit_id}/png/img{i}.png")["v"].filter(
                        "scale", screenshot_width, -1
                    )
                )
                background_clip = background_clip.overlay(
                    image_clips[i],
                    enable=f"between(t,{current_time},{current_time + audio_clips_durations[i]})",
                    x="(main_w-overlay_w)/2",
                    y="(main_h-overlay_h)/2",
                )
                current_time += audio_clips_durations[i]
    else:
        for i in range(0, number_of_clips + 1):
            image_clips.append(
                ffmpeg.input(f"assets/temp/{reddit_id}/png/comment_{i}.png")["v"]
                .filter("scale", screenshot_width, -1)
                # .filter("zoompan", zoom="if(lte(zoom,1.0),1.5,max(1.5,zoom))", x="(iw-ow)/2", y="(ih-oh)/2", d="1", fps="30")
            )
            image_overlay = image_clips[i].filter("colorchannelmixer", aa=opacity)
            # background_clip = background_clip.overlay(
            #     image_overlay,
            #     enable=f"between(t,{current_time},{current_time + audio_clips_durations[i]})",
            #     x="(main_w-overlay_w)/2",
            #     y="(main_h-overlay_h)/2",
            # )
            background_clip = background_clip.overlay(
                image_overlay,
                enable=f"between(t,{current_time},{current_time + audio_clips_durations[i]})",
                x="(main_w-overlay_w)/2",
                y="(main_h-overlay_h-100)",
            )

            fontSize = 96
            comment_body = reddit_obj['thread_title_en'] if i == 0 else reddit_obj["comments"][i - 1]["comment_body"]
            max_text_width = main_w - 50  # 假设文字距离视频边界有一定的间距
            background_clip = background_clip.drawtext(
                text=wrap_text(comment_body, fontSize, max_text_width),
                fontfile=os.path.join("fonts", "A-站酷仓耳渔阳体-700-W05.ttf"),
                fontsize=fontSize,
                fontcolor="yellow",  # 设置字体颜色为黄色
                box=1,  # 启用字体边框
                boxcolor="black",  # 设置字体边框颜色为黑色
                boxborderw=5,  # 设置字体边框宽度
                x="(main_w-text_w)/2",
                y="(main_h-text_h)",
                enable=f"between(t,{current_time},{current_time + audio_clips_durations[i]})"
            )
            current_time += audio_clips_durations[i]



    title = re.sub(r"[^\w\s-]", "", reddit_obj["thread_title"])
    idx = re.sub(r"[^\w\s-]", "", reddit_obj["thread_id"])
    title_thumb = reddit_obj["thread_title"]

    filename = f"{name_normalize(title)[:251]}"
    subreddit = settings.config["reddit"]["thread"]["subreddit"]

    if not exists(f"./results/{subreddit}"):
        print_substep(
            "The 'results' folder could not be found so it was automatically created."
        )
        os.makedirs(f"./results/{subreddit}")

    if not exists(f"./results/{subreddit}/OnlyTTS") and allowOnlyTTSFolder:
        print_substep(
            "The 'OnlyTTS' folder could not be found so it was automatically created."
        )
        os.makedirs(f"./results/{subreddit}/OnlyTTS")

    # create a thumbnail for the video
    settingsbackground = settings.config["settings"]["background"]

    if settingsbackground["background_thumbnail"]:
        if not exists(f"./results/{subreddit}/thumbnails"):
            print_substep(
                "The 'results/thumbnails' folder could not be found so it was automatically created."
            )
            os.makedirs(f"./results/{subreddit}/thumbnails")
        # get the first file with the .png extension from assets/backgrounds and use it as a background for the thumbnail
        first_image = next(
            (
                file
                for file in os.listdir("assets/backgrounds")
                if file.endswith(".png")
            ),
            None,
        )
        if first_image is None:
            print_substep("No png files found in assets/backgrounds", "red")

        else:
            font_family = settingsbackground["background_thumbnail_font_family"]
            font_size = settingsbackground["background_thumbnail_font_size"]
            font_color = settingsbackground["background_thumbnail_font_color"]
            thumbnail = Image.open(f"assets/backgrounds/{first_image}")
            width, height = thumbnail.size
            thumbnailSave = create_thumbnail(
                thumbnail,
                font_family,
                font_size,
                font_color,
                width,
                height,
                title_thumb,
            )
            thumbnailSave.save(f"./assets/temp/{reddit_id}/thumbnail.png")
            print_substep(
                f"Thumbnail - Building Thumbnail in assets/temp/{reddit_id}/thumbnail.png"
            )

    text = f"Background by {background_config['video'][2]}"
    background_clip = ffmpeg.drawtext(
        background_clip,
        text='老外看中国',
        x="(w-text_w-100)",  # 将文本定位在右侧
        y=100,  # 将文本定位在顶部
        fontsize=100,
        fontcolor="White",
        fontfile=os.path.join("fonts", "A-站酷仓耳渔阳体-700-W05.ttf"),
    )


    background_clip = ffmpeg.drawtext(
        background_clip,
        text=reddit_obj['thread_title'],
        x=100,
        y=100,
        fontsize=100,
        fontcolor="White",
        fontfile=os.path.join("fonts", "A-站酷仓耳渔阳体-700-W05.ttf"),
        # x=100,  # 调整x坐标以控制文字在左侧的位置
        # y="(h-text_h)/2",  # 将文字垂直居中放置
        # rotate=90,  # 将文字旋转90度以垂直显示
    )

    # 添加第二段文本
    # background_clip = ffmpeg.drawtext(
    #     background_clip,
    #     text=reddit_obj['thread_title'],
    #     # x=f"(w-text_w)",
    #     # y=f"(h-text_h)",
    #     fontsize=100,
    #     fontcolor="White",
    #     fontfile=os.path.join("fonts", "A-站酷仓耳渔阳体-700-W05.ttf"),
    #     x=200,  # 调整x坐标以控制文字在左侧的位置
    #     y="(h-text_h)/2",  # 将文字垂直居中放置
    #     rotate=90,  # 将文字旋转90度以垂直显示
    # )

    # background_clip = ffmpeg.drawtext(
    #     background_clip,
    #     text=reddit_obj['thread_title'],
    #     fontfile=os.path.join("fonts", "A-站酷仓耳渔阳体-700-W05.ttf"),
    #     fontsize=96,
    #     fontcolor="yellow",  # 设置字体颜色为黄色
    #     box=1,  # 启用字体边框
    #     boxcolor="black",  # 设置字体边框颜色为黑色
    #     boxborderw=5,  # 设置字体边框宽度
    #     x="20",
    #     y="(main_h-text_h)*1/3",
    #     enable=f"between(t,{current_time},{current_time + audio_clips_durations[i]})",
    #     rotate=90,  # 将文本旋转90度以竖排显示
    # )


    background_clip = background_clip.filter("scale", W, H)
    print_step("Rendering the video 🎥")
    from tqdm import tqdm

    pbar = tqdm(total=100, desc="Progress: ", bar_format="{l_bar}{bar}", unit=" %")

    def on_update_example(progress) -> None:
        status = round(progress * 100, 2)
        old_percentage = pbar.n
        pbar.update(status - old_percentage)

    defaultPath = f"results/{subreddit}"
    with ProgressFfmpeg(length, on_update_example) as progress:
        path = defaultPath + f"/{filename}"
        path = (
            path[:251] + ".mp4"
        )  # Prevent a error by limiting the path length, do not change this.
        ffmpeg.output(
            background_clip,
            final_audio,
            path,
            f="mp4",
            **{
                "c:v": "h264",
                "b:v": "20M",
                "b:a": "192k",
                "threads": multiprocessing.cpu_count(),
            },
        ).overwrite_output().global_args("-progress", progress.output_file.name).run(
            quiet=True,
            overwrite_output=True,
            capture_stdout=False,
            capture_stderr=False,
        )
    old_percentage = pbar.n
    pbar.update(100 - old_percentage)
    if allowOnlyTTSFolder:
        path = defaultPath + f"/OnlyTTS/{filename}"
        path = (
            path[:251] + ".mp4"
        )  # Prevent a error by limiting the path length, do not change this.
        print_step("Rendering the Only TTS Video 🎥")
        with ProgressFfmpeg(length, on_update_example) as progress:
            try:
                ffmpeg.output(
                    background_clip,
                    audio,
                    path,
                    f="mp4",
                    **{
                        "c:v": "h264",
                        "b:v": "20M",
                        "b:a": "192k",
                        "threads": multiprocessing.cpu_count(),
                    },
                ).overwrite_output().global_args("-progress", progress.output_file.name).run(
                    quiet=True,
                    overwrite_output=True,
                    capture_stdout=False,
                    capture_stderr=False,
                )
            except ffmpeg.Error as e:
                print(e.stderr.decode("utf8"))
                exit(1)

        old_percentage = pbar.n
        pbar.update(100 - old_percentage)
    pbar.close()
    save_data(subreddit, filename + ".mp4", title, idx, background_config["video"][2])
    print_step("Removing temporary files 🗑")
    cleanups = cleanup(reddit_id)
    print_substep(f"Removed {cleanups} temporary files 🗑")
    print_step("Done! 🎉 The video is in the results folder 📁")
