from asyncio import run
from datetime import date
from time import monotonic

from httpx import AsyncClient

from .auth import auth
from .room import RoomAPI


async def main() -> None:
    async with AsyncClient() as client:
        await auth(client, input("username >> "), input("password >> "))
        api = await RoomAPI.build(client)

        for n in (2, 5, 10, 20, 50):
            t_start = monotonic()
            await api.fetch_bookings(date.today(), rooms_per_page=n)
            print(f"{n = }, {monotonic()- t_start: .2f} s.")


run(main())
