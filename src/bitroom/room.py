from __future__ import annotations

import datetime
from json import dumps
from math import ceil
from typing import TYPE_CHECKING, TypedDict

from requests.utils import dict_from_cookiejar
from rich.progress import track

if TYPE_CHECKING:
    from typing import Generator

    from requests import Response, Session

API_BASE = "http://stu.bit.edu.cn"


def prepare_headers(session: Session) -> None:
    """准备请求头

    设置 cookie 等。
    """

    session.get(
        f"{API_BASE}/xsfw/sys/swpubapp/indexmenu/getAppConfig.do?appId=4974886768205231&appName=cdyyapp"
    )
    cookie = dict_from_cookiejar(session.cookies)

    session.headers.update(
        {
            "Referer": f"{API_BASE}/xsfw/sys/cdyyapp/*default/index.do",
            "Cookie": "; ".join(f"{key}={value}" for key, value in cookie.items()),
        }
    )


def parse_time_range(time_range: str) -> tuple[datetime.time, datetime.time]:
    """解释时间区间

    # 例子

    ```
    from datetime import time

    assert parse_time_range('08:00-08:45') == (time(8, 0), time(8, 45))
    ```
    """

    parts = time_range.split("-")
    assert len(parts) == 2, f"Invalid time range: “{time_range}”"
    return tuple(datetime.time.fromisoformat(t) for t in parts)


class Booking(TypedDict):
    """可预约的时空区间"""

    room_name: str
    room_id: str
    time: tuple[datetime.datetime, datetime.datetime]
    """(开始时刻, 结束时刻)"""


class RoomAPI:
    """场地预约 API 包装"""

    _session: Session

    def __init__(self, session: Session) -> None:
        """
        :param session: 已登录的 session，用于后续所有网络请求（会被修改）
        """

        prepare_headers(session)
        self._session = session

    def _post(self, url_path: str, *args, **kwargs) -> Response:
        return self._session.post(f"{API_BASE}{url_path}", *args, **kwargs)

    def _get_data(self, date: datetime.date, page: int, rooms_per_page: int) -> dict:
        """
        :param date: 日期
        :param page: 第几页，从0开始
        :param rooms_per_page: 每页房间数量
        :return: 相邻一周（周一–周日）的预约情况
        """

        res = self._post(
            "/xsfw/sys/cdyyapp/modules/CdyyApplyController/getSiteInfo.do",
            {
                "data": dumps(
                    {
                        # 预约日期
                        "YYRQ": date.isoformat(),
                        "pageNumber": page + 1,
                        "pageSize": rooms_per_page,
                    }
                )
            },
        )
        res.raise_for_status()
        json = res.json()
        assert json["code"] == "0" and json["msg"] == "成功"

        return json["data"]

    def get_bookings(
        self, date: datetime.date, *, rooms_per_page=10
    ) -> Generator[Booking, None, None]:
        """获取可预约的时空区间

        :param date: 日期
        :param rooms_per_page: 访问 API 时每页房间数量
        :yield: 相邻一周（周一–周日）可预约的时空区间
        """

        # 首先试探，取得基本数据
        # 只获取一项响应更快
        sniff_data = self._get_data(date, page=0, rooms_per_page=1)

        dates = [date.fromisoformat(it["WEEKDATE"]) for it in sniff_data["weekList"]]
        """此次查询涉及的日期，周一–周日"""

        n_rooms = int(sniff_data["siteInfoList"][0]["totalCount"])
        n_pages = ceil(n_rooms / rooms_per_page)

        # 然后获取所有数据
        # 每一页
        for p in track(range(n_pages), description="Fetching data…"):
            data = self._get_data(date, page=p, rooms_per_page=rooms_per_page)

            # 每个房间
            for room in data["siteInfoList"]:
                # 每一天
                for date_status in room["currentWeekData"]:
                    if date_status["isLock"] or date_status["applyTime"] == "":
                        continue

                    # 每个时段
                    for time_range in date_status["applyTime"].split(","):
                        yield Booking(
                            room_name=room["CDMC"],
                            room_id=room["CDDM"],
                            time=tuple(
                                datetime.datetime.combine(
                                    dates[date_status["XQJ"] - 1], t
                                )
                                for t in parse_time_range(time_range)
                            ),
                        )
