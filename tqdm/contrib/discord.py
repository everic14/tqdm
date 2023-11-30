from os import getenv
from warnings import warn

import requests

from ..auto import tqdm as tqdm_auto
from ..std import TqdmWarning
from .utils_worker import MonoWorker
from ..version import __version__

__author__ = {"github.com/": ["casperdcl"]}
__all__ = ["DiscordIO", "tqdm_discord", "ddrange", "tqdm", "drange"]


class DiscordIO(MonoWorker):
    """Non-blocking file-like IO using a Discord Bot."""

    API = "https://discord.com/api/v10"

    def __init__(self, token, channel_id):
        """Creates a new message in the given `channel_id`."""
        super(DiscordIO, self).__init__()
        self.token = token
        self.channel_id = channel_id
        self.text = self.__class__.__name__
        self.message_id

    @property
    def message_id(self):
        if hasattr(self, "_message_id"):
            return self._message_id
        try:
            headers = {
                "Authorization": f"Bot {self.token}",
                "User-Agent": f"TQDM Discord progress bar (http://github.com/tqdm/tqdm, {__version__})",
            }
            data = {"content": "`" + self.text + "`"}
            res = requests.post(
                f"{self.API}/channels/{self.channel_id}/messages",
                headers=headers,
                json=data,
            ).json()
        except Exception as e:
            tqdm_auto.write(str(e))
        else:
            if "id" in res:
                self._message_id = res["id"]
                return self._message_id

    def write(self, s):
        """Replaces internal `message_id`'s text with `s`."""
        if not s:
            s = "..."
        s = s.replace("\r", "").strip()
        if s == self.text:
            return  # avoid duplicate message Bot error
        message_id = self.message_id
        if message_id is None:
            return
        self.text = s
        try:
            headers = {
                "Authorization": f"Bot {self.token}",
                "User-Agent": f"TQDM Discord progress bar (http://github.com/tqdm/tqdm, {__version__})",
            }
            data = {"content": "`" + s + "`"}
            future = self.submit(
                requests.patch,
                f"{self.API}/channels/{self.channel_id}/messages/{message_id}",
                headers=headers,
                json=data,
            )
        except Exception as e:
            tqdm_auto.write(str(e))
        else:
            return future

    def delete(self):
        """Deletes internal `message_id`."""
        try:
            headers = {
                "Authorization": f"Bot {self.token}",
                "User-Agent": f"TQDM Discord progress bar (http://github.com/tqdm/tqdm, {__version__})",
            }
            future = self.submit(
                requests.delete,
                f"{self.API}/channels/{self.channel_id}/messages/{self.message_id}",
                headers=headers,
            )
        except Exception as e:
            tqdm_auto.write(str(e))
        else:
            return future


class tqdm_discord(tqdm_auto):
    """
    Standard `tqdm.auto.tqdm` but also sends updates to a Discord Bot.
    May take a few seconds to create (`__init__`).

    >>> from tqdm.contrib.discord import tqdm, drange
    >>> for i in tqdm(iterable, token='{token}', channel_id='{channel_id}'):
    ...     ...
    """

    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        token  : str, required. Discord bot token
            [default: ${TQDM_DISCORD_TOKEN}].
        channel_id  : str, required. Discord channel ID
            [default: ${TQDM_DISCORD_CHANNEL_ID}].

        See `tqdm.auto.tqdm.__init__` for other parameters.
        """
        if not kwargs.get("disable"):
            kwargs = kwargs.copy()
            self.dio = DiscordIO(
                kwargs.pop("token", getenv("TQDM_DISCORD_TOKEN")),
                kwargs.pop("channel_id", getenv("TQDM_DISCORD_CHANNEL_ID")),
            )
        super(tqdm_discord, self).__init__(*args, **kwargs)

    def display(self, **kwargs):
        super(tqdm_discord, self).display(**kwargs)
        fmt = self.format_dict
        if fmt.get("bar_format", None):
            fmt["bar_format"] = (
                fmt["bar_format"]
                .replace("<bar/>", "{bar:10u}")
                .replace("{bar}", "{bar:10u}")
            )
        else:
            fmt["bar_format"] = "{l_bar}{bar:10u}{r_bar}"
        self.dio.write(self.format_meter(**fmt))

    def clear(self, *args, **kwargs):
        super(tqdm_discord, self).clear(*args, **kwargs)
        if not self.disable:
            self.dio.write("")

    def close(self):
        if self.disable:
            return
        super(tqdm_discord, self).close()
        if not (self.leave or (self.leave is None and self.pos == 0)):
            self.dio.delete()


def ddrange(*args, **kwargs):
    """Shortcut for `tqdm.contrib.discord.tqdm(range(*args), **kwargs)`."""
    return tqdm_discord(range(*args), **kwargs)


# Aliases
tqdm = tqdm_discord
drange = ddrange
