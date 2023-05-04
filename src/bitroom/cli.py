from asyncio import run
from datetime import date

import click
from httpx import AsyncClient
from sys import exit

from . import Booking, RoomAPI, auth
from .config import Config, read_config
from .config import config_paths as _config_paths


@click.group()
@click.version_option()
def cli() -> None:
    """BIT 场地预约查询接口"""
    pass


@cli.command()
def config_paths() -> None:
    """列出配置文件可能的位置"""
    click.echo("\n".join(map(str, _config_paths())))


async def _show(config: Config) -> list[Booking]:
    async with AsyncClient() as client:
        await auth(client, config.username, config.password)
        api = await RoomAPI.build(client)

        return await api.fetch_bookings(date.today())


@cli.command()
@click.option(
    "--auth",
    type=str,
    help="认证信息，形如“1120771210:cyberpunk”（<学号>:<密码>）；不建议使用，请改用配置文件",
)
def show(auth: str | None):
    """显示所有可预约的时空区间"""

    config = read_config()
    if auth is not None:
        click.echo(
            f"{click.style('[Warning]', fg='yellow')} "
            "不建议使用 --auth，这会让密码出现在命令行历史记录中，更容易泄露。请改用配置文件。"
        )

        username, password = auth.split(":", maxsplit=1)
        if config is None:
            config = Config(username, password)
        else:
            config.username = username
            config.password = password

    if config is None:
        click.echo(
            f"{click.style('[Error]', fg='red')} "
            "未提供学号、密码，将无法认证。请填写配置文件。（可用 bitroom config-paths 查看文件位置）"
        )
        exit(1)

    bookings = run(_show(config))
    print(*bookings, sep="\n")
