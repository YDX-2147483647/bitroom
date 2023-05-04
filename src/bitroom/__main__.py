from datetime import date
from time import monotonic

from httpx import Client
from rich.pretty import pprint

from .auth import auth
from .room import RoomAPI

client = Client()
auth(client, input("username >> "), input("password >> "))
api = RoomAPI(client)


for n in (2, 5, 10, 20, 50):
    t_start = monotonic()
    for booking in api.get_bookings(date.today(), rooms_per_page=n):
        pprint(booking)
    pprint(f"{n = }, {monotonic()- t_start: .2f} s.")
