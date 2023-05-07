"""Terminal user interface

Dependencies in group “tui” are required.
"""

from __future__ import annotations

from datetime import date
from json import load
from pathlib import Path
from time import sleep
from typing import TYPE_CHECKING

from httpx import AsyncClient
from more_itertools import chunked
from textual import on, work
from textual.app import App
from textual.widgets import Footer, Header, Input, OptionList
from textual.widgets.option_list import Option
from textual.worker import get_current_worker

from . import Booking, RoomAPI, auth
from .config import read_config

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from .config import Config


class RoomApp(App):
    """App to interact with RoomAPI"""

    BINDINGS = [
        ("d", "toggle_dark", "Dark/切换深色模式"),
        ("q", "quit", "Quit/退出"),
        ("r", "refresh_bookings", "Refresh/刷新数据"),
    ]

    config: Config
    bookings: list[Booking]

    def __init__(self) -> None:
        super().__init__()

        config = read_config()
        assert config is not None
        self.config = config

        with Path("bookings.json").open(encoding="utf-8") as f:
            self.bookings = list(map(Booking.from_dict, load(f)))

    def compose(self) -> ComposeResult:
        yield Header()

        yield Input(placeholder="Enter a City", id="search")
        yield OptionList(*map(str, self.bookings), id="bookings")
        # todo: display more info

        yield Footer()

    def action_toggle_dark(self) -> None:
        """切换深色模式"""
        self.dark = not self.dark

    @on(Input.Changed, "#search")
    def search(self, message: Input.Changed) -> None:
        """搜索

        搜索很快，但更新界面很慢，因此使用 worker 防抖。
        """
        self._search(message.value)

    @work(exclusive=True)
    def _search(self, keyword: str) -> None:
        worker = get_current_worker()

        self.log(f"Receive keyword “{keyword}”, and debounce for 0.5 s.")
        sleep(0.5)

        if worker.is_cancelled:
            self.log(f"The search for “{keyword}” is cancelled.")
            return
        self.log(f"Start searching for “{keyword}”…")

        # todo: More advanced search
        result = (b for b in self.bookings if all(k in str(b) for k in keyword.split()))

        option_list = self.query_one("#bookings", OptionList)

        if worker.is_cancelled:
            self.log(f"The search for “{keyword}” finished, but had been cancelled.")
            return

        option_list.clear_options()

        # `option_list.add_option()` always refreshes the widget, which can be slow.
        # https://github.com/Textualize/textual/blob/14850d54a3f5fed878cff1ce2f5da08503a02932/src/textual/widgets/_option_list.py#L511-L531
        #
        # Here we add 100 options, refresh, add another 100, refresh, and so on.
        for bookings_group in chunked(result, 100):
            if worker.is_cancelled:
                self.log(f"The search for “{keyword}” is cancelled halfway.")
                return

            for b in bookings_group:
                content = option_list._make_content(str(b))
                option_list._contents.append(content)
                if isinstance(content, Option):
                    option_list._options.append(content)

            option_list._refresh_content_tracking(force=True)
            option_list.refresh()

        self.log(f"Finish the search for “{keyword}”.")

    async def action_refresh_bookings(self) -> None:
        """刷新 bookings 数据"""
        self._refresh_bookings()

    @work(exclusive=True)
    async def _refresh_bookings(self) -> None:
        self.log("Start refreshing bookings…")

        # 因刷新并不频繁，并不保持登录，而是每次重新登录。
        async with AsyncClient() as client:
            await auth(client, self.config.username, self.config.password)
            api = await RoomAPI.build(client)

            self.bookings = await api.fetch_bookings(date.today())
            self.log("Bookings data is refreshed.")

            # Refresh search result
            self._search(self.query_one("#search", Input).value)


if __name__ == "__main__":
    app = RoomApp()
    app.run()
