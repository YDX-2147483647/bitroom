from __future__ import annotations

import datetime
from asyncio import gather
from dataclasses import asdict, dataclass
from itertools import chain
from json import dumps
from math import ceil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Generator, Mapping

    from httpx import AsyncClient, Response

API_BASE = "http://stu.bit.edu.cn"


async def prepare_headers(client: AsyncClient) -> None:
    """准备请求头

    设置 cookie 等。
    """

    # Get cookie
    res = await client.get(
        f"{API_BASE}/xsfw/sys/swpubapp/indexmenu/getAppConfig.do?appId=4974886768205231&appName=cdyyapp",
        follow_redirects=True,
    )
    res.raise_for_status()

    client.headers.update(
        {
            "Referer": f"{API_BASE}/xsfw/sys/cdyyapp/*default/index.do",
        }
    )


def parse_time_range(time_range: str) -> tuple[datetime.time, datetime.time]:
    """解释时间区间

    `format_time_range`的逆。

    # 例子

    ```
    from datetime import time

    assert parse_time_range('08:00-08:45') == (time(8, 0), time(8, 45))
    ```
    """

    parts = time_range.split("-")
    assert len(parts) == 2, f"Invalid time range: “{time_range}”"
    return tuple(datetime.time.fromisoformat(t) for t in parts)


def format_time_range(time_range: tuple[datetime.time, datetime.time]) -> str:
    """格式化时间区间

    `parse_time_range`的逆。

    # 例子

    ```
    from datetime import time

    assert format_time_range((time(8, 0), time(8, 45))) == '08:00-08:45'
    ```
    """

    return "-".join(t.isoformat(timespec="minutes") for t in time_range)


def format_datetime_range(time: tuple[datetime.datetime, datetime.datetime]) -> str:
    """格式化时间区间

    含日期。
    """

    if time[0].date() == time[1].date():
        return (
            time[0].isoformat(sep=" ", timespec="minutes")
            + "–"
            + time[1].time().isoformat(timespec="minutes")
        )
    else:
        return "–".join(t.isoformat(sep=" ", timespec="minutes") for t in time)


@dataclass
class Booking:
    """可预约的时空区间"""

    room_name: str
    room_id: str
    t_start: datetime.datetime
    """开始时刻"""
    t_end: datetime.datetime
    """结束时刻"""

    def __str__(self) -> str:
        return (
            f"<Booking [{self.room_name}] "
            f"{format_datetime_range((self.t_start,self.t_end))}>"
        )

    def as_dict(self) -> dict[str, str]:
        raw = asdict(self)
        for k, v in raw.items():
            if isinstance(v, datetime.datetime):
                raw[k] = v.isoformat()

        return raw

    @classmethod
    def from_dict(cls, raw: dict[str, str | datetime.datetime]) -> Booking:
        for k, v in raw.items():
            if k.startswith("t_") and isinstance(v, str):
                raw[k] = datetime.datetime.fromisoformat(v)

        return Booking(**raw)


class RoomAPI:
    """场地预约 API 包装

    ## 例子

    ```
    from datetime import date

    api = await RoomAPI.build(client)
    bookings = await api.get_bookings(date.today())
    await api.book(bookings[0], tel="13806491023", applicant="Boltzmann")
    ```
    """

    _client: AsyncClient

    @classmethod
    async def build(cls, client: AsyncClient) -> RoomAPI:
        """
        :param client: 已登录的 client，用于后续所有网络请求（会被修改）
        """

        await prepare_headers(client)
        return RoomAPI(client)

    def __init__(self, client: AsyncClient) -> None:
        """
        请使用`build`。
        """

        self._client = client

    async def _post(
        self, url_path: str, data: Mapping[str, Any] | None = None, **kwargs
    ) -> Response:
        return await self._client.post(
            f"{API_BASE}{url_path}",
            data={"data": dumps(data)},
            **kwargs,
        )

    async def _fetch_bookings_data(
        self, date: datetime.date, page: int, *, rooms_per_page: int
    ) -> dict:
        """Get a page of data
        :param date: 日期
        :param page: 第几页，从0开始
        :param rooms_per_page: 每页房间数量
        :return: 相邻一周（周一–周日）的预约情况
        """

        res = await self._post(
            "/xsfw/sys/cdyyapp/modules/CdyyApplyController/getSiteInfo.do",
            data={
                # 预约日期
                "YYRQ": date.isoformat(),
                "pageNumber": page + 1,
                "pageSize": rooms_per_page,
            },
            timeout=max(20, 20 * rooms_per_page),  # Yes, it's really slow…
            follow_redirects=True,
        )
        res.raise_for_status()
        json = res.json()
        assert json["code"] == "0" and json["msg"] == "成功"

        return json["data"]

    def _parse_bookings_data(
        self, data: dict, *, dates: list[datetime.date]
    ) -> Generator[Booking, None, None]:
        """Parse a page of data to bookings
        :param data: API 的原始响应
        :param dates: 涉及的日期，周一–周日
        """

        # 每个房间
        for room in data["siteInfoList"]:
            # 每一天
            for date_status in room["currentWeekData"]:
                if date_status["isLock"] or date_status["applyTime"] == "":
                    continue

                # 每个时段
                for time_range in date_status["applyTime"].split(","):
                    t_start, t_end = (
                        # XQJ = 星期几
                        datetime.datetime.combine(dates[date_status["XQJ"] - 1], t)
                        for t in parse_time_range(time_range)
                    )
                    yield Booking(
                        room_name=room["CDMC"],  # 场地名称
                        room_id=room["CDDM"],  # 场地代码
                        t_start=t_start,
                        t_end=t_end,
                    )

    async def _fetch_bookings_page(
        self,
        page: int,
        *,
        date: datetime.date,
        rooms_per_page: int,
        dates: list[datetime.date],
    ) -> list[Booking]:
        """Fetch a page of bookings

        :param date: 日期
        :param page: 第几页，从0开始
        :param rooms_per_page: 每页房间数量
        :param dates: 涉及的日期，周一–周日
        """

        data = await self._fetch_bookings_data(
            date, page=page, rooms_per_page=rooms_per_page
        )
        return list(self._parse_bookings_data(data, dates=dates))

    async def fetch_bookings(
        self,
        date: datetime.date,
        *,
        rooms_per_page=3,
        n_weeks=2,
    ) -> list[Booking]:
        """获取可预约的时空区间

        :param date: 日期
        :param rooms_per_page: 访问 API 时每页房间数量
        :param n_weeks: 获取的时间范围，1 代表只获取相邻一周，2 代表相邻一周和再下一周
        :yield: 相邻几周可预约的时空区间

        “相邻一周”指周一–周日。
        例如假设5月1日为周一，查询 5月5日，则会返回5月1–7日的情况。

        # 玄学

        响应时间与 rooms_per_page 近似线性正相关。

        若不并发，rooms_per_page=10 时单位时间获取的房间最多。
        """

        # 首先试探，取得基本数据
        # 只获取一项响应更快
        sniff_data = await self._fetch_bookings_data(date, page=0, rooms_per_page=1)

        dates = [date.fromisoformat(it["WEEKDATE"]) for it in sniff_data["weekList"]]
        """此次查询相邻一周的日期，周一–周日"""

        n_rooms = int(sniff_data["siteInfoList"][0]["totalCount"])
        n_pages = ceil(n_rooms / rooms_per_page)

        # 然后获取所有数据
        fetch_plans = []
        # 每一周
        for w in range(n_weeks):
            shift = datetime.timedelta(weeks=w)
            shifted_date = date + shift
            shifted_dates = [d + shift for d in dates]

            fetch_plans.extend(
                self._fetch_bookings_page(
                    page=p,
                    date=shifted_date,
                    rooms_per_page=rooms_per_page,
                    dates=shifted_dates,
                )
                for p in range(n_pages)
            )

        # 每一页的结果
        bookings_set = await gather(*fetch_plans)

        # Flatten
        return list(chain.from_iterable(bookings_set))

    async def book(
        self,
        booking: Booking | list[Booking],
        *,
        tel: str,
        applicant: str,
        description: str | None = None,
        remark: str | None = None,
    ) -> None:
        """预约

        :param booking: 要预约的时空区间，可多个，但必须同一天、同一房间
        :param tel: 联系电话
        :param applicant: 申请人姓名
        :param description: 申请陈述
        :param remark: 备注
        """

        bookings = booking if isinstance(booking, list) else [booking]
        assert all(
            b.room_id == bookings[0].room_id
            and b.t_start.date() == bookings[0].t_start.date()
            for b in bookings
        ), f"预约必须不是同一天、同一房间，请分多次预约：{bookings}"

        res = await self._post(
            "/xsfw/sys/cdyyapp/modules/CdyyApplyController/saveReserveSite.do",
            data={
                # 场地代码-显示
                "CDDM_DISPLAY": bookings[0].room_name,
                # 场地代码
                "CDDM": bookings[0].room_id,
                # 预约日期
                "YYRQ": bookings[0].t_start.date().isoformat(),
                # 使用时段
                "SYSD": ",".join(
                    format_time_range((b.t_start.time(), b.t_end.time()))
                    for b in bookings
                ),
                # 申请陈述
                "SQCS": description or "",
                # 备注
                "BZ": remark or "",
                # 联系电话
                "LXDH": tel,
                # 申请人姓名
                "SQRXM": applicant,
                # 单位代码（无用）
                "DWDM": "299792458",  # 光在真空中的速率（m/s）
                # 申请编码（无用）
                "SQBM": "",
                # 审核状态（无用）
                "SHZT": "90",
            },
        )

        res.raise_for_status()
        json = res.json()
        # 似乎服务端没验证，永远成功
        assert json["code"] == "0" and json["msg"] == "成功"
