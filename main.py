#!/usr/bin/env python
import math
import sys
from os import name
from pathlib import Path
from subprocess import Popen
from typing import NoReturn

from prawcore import ResponseException
from utils.console import print_substep
from reddit.subreddit import get_subreddit_threads
from utils import settings
from utils.cleanup import cleanup
from utils.console import print_markdown, print_step
from utils.id import id
from utils.version import checkversion
from video_creation.background import (
    download_background_video,
    download_background_audio,
    chop_background,
    get_background_config,
)
from video_creation.final_video import make_final_video, after_final_video
from video_creation.screenshot_downloader import get_screenshots_of_reddit_posts,take_screenshot_ray
from video_creation.voices import save_text_to_mp3
from utils.ffmpeg_install import ffmpeg_install

__VERSION__ = "3.2"

print(
    """
██████╗ ███████╗██████╗ ██████╗ ██╗████████╗    ██╗   ██╗██╗██████╗ ███████╗ ██████╗     ███╗   ███╗ █████╗ ██╗  ██╗███████╗██████╗
██╔══██╗██╔════╝██╔══██╗██╔══██╗██║╚══██╔══╝    ██║   ██║██║██╔══██╗██╔════╝██╔═══██╗    ████╗ ████║██╔══██╗██║ ██╔╝██╔════╝██╔══██╗
██████╔╝█████╗  ██║  ██║██║  ██║██║   ██║       ██║   ██║██║██║  ██║█████╗  ██║   ██║    ██╔████╔██║███████║█████╔╝ █████╗  ██████╔╝
██╔══██╗██╔══╝  ██║  ██║██║  ██║██║   ██║       ╚██╗ ██╔╝██║██║  ██║██╔══╝  ██║   ██║    ██║╚██╔╝██║██╔══██║██╔═██╗ ██╔══╝  ██╔══██╗
██║  ██║███████╗██████╔╝██████╔╝██║   ██║        ╚████╔╝ ██║██████╔╝███████╗╚██████╔╝    ██║ ╚═╝ ██║██║  ██║██║  ██╗███████╗██║  ██║
╚═╝  ╚═╝╚══════╝╚═════╝ ╚═════╝ ╚═╝   ╚═╝         ╚═══╝  ╚═╝╚═════╝ ╚══════╝ ╚═════╝     ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
"""
)
# Modified by JasonLovesDoggo
print_markdown(
    "### Thanks for using this tool! Feel free to contribute to this project on GitHub! If you have any questions, feel free to join my Discord server or submit a GitHub issue. You can find solutions to many common problems in the documentation: https://reddit-video-maker-bot.netlify.app/"
)
checkversion(__VERSION__)


def main(POST_ID=None) -> None:
    global redditid, reddit_object
    reddit_object = {
        "thread_url": "https://www.quora.com/How-can-I-copy-a-whole-webpage-all-of-the-code",
        "thread_title": "中国火锅好吃吗",
        "thread_title_en": "Is chinese good?",
        "thread_id": "abcdef",
        "is_nsfw": False,
        "comments": [
            {
                "comment_body": "韩国网友：火锅是我们发明的",
                "comment_body_en": "Hotpot is something we Koreans invented.",
                "comment_url": "https://reddit.com/r/test/abcdef/comment/123456",
                "comment_id": "123456"
            },
            {
                "comment_body": "英国网友：这给我的感觉就是特别辣",
                "comment_body_en": "To me, this feels especially spicy.",
                "comment_url": "https://reddit.com/r/test/abcdef/comment/234567",
                "comment_id": "234567"
            },
            {
                "comment_body": "预测式外呼针对任务中已分配名单进行外呼，并不针对未分配名单。",
                "comment_body_en": "Predictive dialing makes outbound calls to lists already assigned to tasks, not unassigned lists.",
                "comment_url": "https://reddit.com/r/test/abcdef/comment/345678",
                "comment_id": "345678"
            },
            {
                "comment_body": "支持配置并发数量（业内大概是接通率30%的情况下,1坐席配2.5-3并发）",
                "comment_body_en": "Concurrency can be configured, with roughly 1 agent handling 2.5-3 concurrent calls at a 30% connection rate.",
                "comment_url": "https://reddit.com/r/test/abcdef/comment/456789",
                "comment_id": "456789"
            },
            {
                "comment_body": "支持配置空闲时间，即当前通话结束后可设置",
                "comment_body_en": "Support for configuring idle time, allowing it to be set after the current call ends.",
                "comment_url": "https://reddit.com/r/test/abcdef/comment/567890",
                "comment_id": "567890"
            },
            {
                "comment_body": "Keep up the good work, everyone!",
                "comment_body_en": "Great job, everyone!",
                "comment_url": "https://reddit.com/r/test/abcdef/comment/678901",
                "comment_id": "678901"
            },
            {
                "comment_body": "Ray is the best!",
                "comment_body_en": "Ray is awesome!",
                "comment_url": "https://reddit.com/r/test/abcdef/comment/789012",
                "comment_id": "789012"
            },
            {
                "comment_body": "I love participating in this community!",
                "comment_body_en": "I enjoy being part of this community!",
                "comment_url": "https://reddit.com/r/test/abcdef/comment/890123",
                "comment_id": "890123"
            },
            {
                "comment_body": "Great thread, keep it up!",
                "comment_body_en": "This thread is fantastic, keep it going!",
                "comment_url": "https://reddit.com/r/test/abcdef/comment/901234",
                "comment_id": "901234"
            },
            {
                "comment_body": "This thread deserves more upvotes!",
                "comment_body_en": "This thread deserves more upvotes!",
                "comment_url": "https://reddit.com/r/test/abcdef/comment/012345",
                "comment_id": "012345"
            }
        ]
    }


    # reddit_object = get_subreddit_threads(POST_ID)

    redditid = id(reddit_object)

    length, number_of_comments = save_text_to_mp3(reddit_object)
    length = math.ceil(length)
    # length = 29
    # number_of_comments = 9
    # take_screenshot_ray(reddit_object)
    # get_screenshots_of_reddit_posts(reddit_object, number_of_comments)
    bg_config = {
        "video": get_background_config("video"),
        "audio": get_background_config("audio"),
    }
    # download_background_video(bg_config["video"])
    # download_background_audio(bg_config["audio"])
    # chop_background(bg_config, length, reddit_object)
    # make_final_video(number_of_comments, length, reddit_object, bg_config)
    after_final_video(reddit_object, bg_config)


def run_many(times) -> None:
    for x in range(1, times + 1):
        print_step(
            f'on the {x}{("th", "st", "nd", "rd", "th", "th", "th", "th", "th", "th")[x % 10]} iteration of {times}'
        )  # correct 1st 2nd 3rd 4th 5th....
        main()
        Popen("cls" if name == "nt" else "clear", shell=True).wait()


def shutdown() -> NoReturn:
    if "redditid" in globals():
        print_markdown("## Clearing temp files")
        cleanup(redditid)
    
    print("Exiting...")
    sys.exit()


if __name__ == "__main__":
    if sys.version_info.major != 3 or sys.version_info.minor != 10:
        print("Hey! Congratulations, you've made it so far (which is pretty rare with no Python 3.10). Unfortunately, this program only works on Python 3.10. Please install Python 3.10 and try again.")
        sys.exit()
    ffmpeg_install()
    directory = Path().absolute()
    config = settings.check_toml(
        f"{directory}/utils/.config.template.toml", f"{directory}/config.toml"
    )
    config is False and sys.exit()
        
    if (
        not settings.config["settings"]["tts"]["tiktok_sessionid"]
        or settings.config["settings"]["tts"]["tiktok_sessionid"] == ""
    ) and config["settings"]["tts"]["voice_choice"] == "tiktok":
        print_substep(
            "TikTok voice requires a sessionid! Check our documentation on how to obtain one.",
            "bold red",
        )
        sys.exit()
    try:
        if config["reddit"]["thread"]["post_id"]:
            for index, post_id in enumerate(
                config["reddit"]["thread"]["post_id"].split("+")
            ):
                index += 1
                print_step(
                    f'on the {index}{("st" if index % 10 == 1 else ("nd" if index % 10 == 2 else ("rd" if index % 10 == 3 else "th")))} post of {len(config["reddit"]["thread"]["post_id"].split("+"))}'
                )
                main(post_id)
                Popen("cls" if name == "nt" else "clear", shell=True).wait()
        elif config["settings"]["times_to_run"]:
            run_many(config["settings"]["times_to_run"])
        else:
            main()
    except KeyboardInterrupt:
        shutdown()
    except ResponseException:
        print_markdown("## Invalid credentials")
        print_markdown("Please check your credentials in the config.toml file")
        shutdown()
    except Exception as err:
        config["settings"]["tts"]["tiktok_sessionid"] = "REDACTED"
        config["settings"]["tts"]["elevenlabs_api_key"] = "REDACTED"
        print_step(
            f"Sorry, something went wrong with this version! Try again, and feel free to report this issue at GitHub or the Discord community.\n"
            f"Version: {__VERSION__} \n"
            f"Error: {err} \n"
            f'Config: {config["settings"]}'
        )
        raise err
