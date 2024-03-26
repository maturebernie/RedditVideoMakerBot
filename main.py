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
        "thread_title": "老外看中国：广州无人公交你敢坐吗？",
        "thread_title_en": "Would you dare to take Guangzhou's driverless bus?",
        "thread_id": "abcdef",
        "is_nsfw": False,
        "comments": [
            {
                "comment_body": "美国网友：我可不会轻易尝试，太危险了。",
                "comment_body_en": "I wouldn't dare to try it, too dangerous.",
                "comment_url": "https://reddit.com/r/test/abcdef/comment/234567",
                "comment_id": "234567"
            },
            {
                "comment_body": "日本网友：这种技术我国早已拥有，不足为奇。",
                "comment_body_en": "We already have this technology in our country, not surprising.",
                "comment_url": "https://reddit.com/r/test/abcdef/comment/345678",
                "comment_id": "345678"
            },
            {
                "comment_body": "韩国网友：这是未来的交通方式，很安全。",
                "comment_body_en": "This is the future of transportation, very safe.",
                "comment_url": "https://reddit.com/r/test/abcdef/comment/123456",
                "comment_id": "123456"
            },
            {
                "comment_body": "印度网友：这对于发展中国家来说是一大进步。",
                "comment_body_en": "This is a big step forward for developing countries like China.",
                "comment_url": "https://reddit.com/r/test/abcdef/comment/456789",
                "comment_id": "456789"
            },
            {
                "comment_body": "俄罗斯网友：中国总是走在时代前列，值得尊敬。",
                "comment_body_en": "China always leads the way in the era, worthy of respect.",
                "comment_url": "https://reddit.com/r/test/abcdef/comment/567890",
                "comment_id": "567890"
            },
            {
                "comment_body": "德国网友：这种创新性技术值得肯定。",
                "comment_body_en": "This innovative technology deserves recognition.",
                "comment_url": "https://reddit.com/r/test/abcdef/comment/678901",
                "comment_id": "678901"
            },
            {
                "comment_body": "加拿大网友：我对这个概念感到很兴奋。",
                "comment_body_en": "I'm excited about this concept.",
                "comment_url": "https://reddit.com/r/test/abcdef/comment/789012",
                "comment_id": "789012"
            },
            {
                "comment_body": "澳大利亚网友：这对于环保是一大利好。",
                "comment_body_en": "This is a big plus for the environment.",
                "comment_url": "https://reddit.com/r/test/abcdef/comment/890123",
                "comment_id": "890123"
            },
            {
                "comment_body": "巴西网友：这对于交通拥堵是一个解决方案。",
                "comment_body_en": "This is a solution to traffic congestion.",
                "comment_url": "https://reddit.com/r/test/abcdef/comment/901234",
                "comment_id": "901234"
            },
            {
                "comment_body": "法国网友：这是未来的交通趋势。",
                "comment_body_en": "This is the future trend of transportation.",
                "comment_url": "https://reddit.com/r/test/abcdef/comment/012345",
                "comment_id": "012345"
            },
            {
                "comment_body": "新加坡网友：我觉得这很酷。",
                "comment_body_en": "I think this is cool.",
                "comment_url": "https://reddit.com/r/test/abcdef/comment/1234567",
                "comment_id": "1234567"
            },
            {
                "comment_body": "意大利网友：我很期待看到这个项目的发展。",
                "comment_body_en": "I look forward to seeing the development of this project.",
                "comment_url": "https://reddit.com/r/test/abcdef/comment/2345678",
                "comment_id": "2345678"
            }
        ]
    }





    # reddit_object = get_subreddit_threads(POST_ID)

    redditid = id(reddit_object)

    length, number_of_comments = save_text_to_mp3(reddit_object)
    length = math.ceil(length)
    # length = 29
    # number_of_comments = 9
    take_screenshot_ray(reddit_object)
    # get_screenshots_of_reddit_posts(reddit_object, number_of_comments)
    bg_config = {
        "video": get_background_config("video"),
        "audio": get_background_config("audio"),
    }
    # download_background_video(bg_config["video"])
    # download_background_audio(bg_config["audio"])
    chop_background(bg_config, length, reddit_object)
    make_final_video(number_of_comments, length, reddit_object, bg_config)
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
