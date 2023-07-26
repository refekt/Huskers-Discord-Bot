from __future__ import annotations

import re

import discord


class Xword:
    __slots__ = [
        "id",
        "seconds",
        "url",
        "userid",
        "xword_date",
    ]

    def __init__(self, message: discord.Message):
        __regex_url: str = r"https:\/\/www\.nytimes\.com\/badges\/games\/mini\.html\?d\=\d{4}\-\d{2}\-\d{2}\&t\=\d{1,4}"

        if __match_url := re.search(__regex_url, message.content.strip()):
            self.url: str | None = __match_url.string
        else:
            self.url = None
            return

        try:
            self.userid: str | None = str(message.author.id)
        except ValueError:
            self.userid = None

        __regex_date: str = r"\d{4}\-\d{2}-\d{2}"

        if __match_date := re.search(__regex_date, self.url):
            self.xword_date: str | None = __match_date.string[
                __match_date.start() : __match_date.end()
            ]
        else:
            self.xword_date = None
        __regex_seconds: str = r"t\=\d{1,5}\&"

        try:
            if __match_seconds := re.search(__regex_seconds, self.url):
                temp: str = __match_seconds.string[
                    __match_seconds.start() : __match_seconds.end()
                ]
                self.seconds: int | None = int(temp[2:-1])
            else:
                self.seconds = None
        except AttributeError:
            self.seconds = 999
            pass
