# 🚩🏠 bitroom (Book an Incongruent Topological Room Or be Out of Mind)

[![PyPI](https://img.shields.io/pypi/v/bitroom?label=PyPI&logo=PyPI&logoColor=white)](https://pypi.org/project/bitroom/)
[![Source GitHub](https://img.shields.io/badge/Source-GitHub-lightgray?logo=github)](https://github.com/YDX-2147483647/bitroom/)
[![Mirror Gitee](https://img.shields.io/badge/Mirror-Gitee-red?logo=gitee)](https://gitee.com/YDX-2147483647/bitroom/)

BIT 场地预约查询接口。

## 💥 源起

- [场地预约系统（桌面版）](http://stu.bit.edu.cn/xsfw/sys/cdyyapp/*default/index.do)的服务器响应太慢了，每次翻页都要十几秒。

  若并发请求，再缓存到本地，会方便不少。

- 房间资源是时空区间，需求常常是“先时间，后空间”；然而也许为方便调度资源、避免冲突，现有系统全都“先空间，后时间”。

  例如，你可能会问：“明天下午还有没有房间？没有的话，后天下午也行。就几个人，也不需要投影。”

  而很少专门针对某一房间问。

bitroom 目前已解决登录、包装 API 等底层问题，可供后来者调用。

## 🧪 例子

### 🤖编程 API

这是主要支持的接口。

```python
from datetime import date
from httpx import AsyncClient
from bitroom import auth, RoomAPI

async with AsyncClient() as client:
    await auth(client, username, password)  # 登录“统一身份认证”
    api = await RoomAPI.build(client)

    # 获取“可预约”的时空区间
    bookings = await api.fetch_bookings(date.today())
    print(bookings[0])

    # 预约
    await api.book(
        bookings[0],
        tel="13806491023",
        applicant="Boltzmann",
        description="Boltzmann 常数是气体的内能与温度的一种比例系数。",
        remark="一般记作 k_B 或 k。",
    )

    # 获取“已预约”的时空区间
    orders = await api.fetch_orders(bookings[0].room_id, date.today())
    print(orders[0])
```

### ⌨️命令行 CLI

也提供了基础的命令行接口，支持查询，不支持预约。

可结合 [fzf](https://github.com/junegunn/fzf/)，搜索日期、时间、房间。（详见 [wiki](https://github.com/YDX-2147483647/bitroom/wiki#-fzf-%E4%BD%BF%E7%94%A8%E7%A4%BA%E4%BE%8B)）

```shell
$ bitroom show | fzf
```

![](https://user-images.githubusercontent.com/73375426/236676121-0bb3f80a-4ef0-4b06-bb03-d41a6f42fe38.png)

详细帮助如下。

（要先`pipx install bitroom`）

```shell
$ bitroom --help
Usage: python -m bitroom [OPTIONS] COMMAND [ARGS]...

  BIT 场地预约查询接口

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  config-paths  列出配置文件可能的位置
  show          显示所有可预约的时空区间
```

```shell
$ bitroom show --help
Usage: python -m bitroom show [OPTIONS]

  显示所有可预约的时空区间

  默认从 API 爬取，因服务器响应慢，大约需 10 s。

      $ bitroom show

  也可直接从 stdin 提供之前的结果。

      $ bitroom show --json > ./bookings.json
      $ cat ./bookings.json | bitroom show

Options:
  --json / --no-json  按 JSON 格式输出
  --auth TEXT         认证信息，形如“1120771210:cyberpunk”（<学号>:<密码>）；不建议使用，请改用配置文件
  --help              Show this message and exit.
```

```shell
$ bitroom show
<Booking [【睿信书院】静c-鸿远报告厅] 2023-05-07 16:00–16:45>
<Booking [【睿信书院】静c-鸿远报告厅] 2023-05-07 19:20–20:05>
<Booking [【精工书院】研讨室1] 2023-05-04 12:15–13:20>
<Booking [【睿信书院】静c-自控会议室] 2023-05-04 13:20–14:05>
<Booking [甘棠社区-102春·事定（Multi-function Room）] 2023-05-05 21:00–22:00>
<Booking [甘棠社区-102春·事定（Multi-function Room）] 2023-05-06 13:20–14:05>
<Booking [甘棠社区-102春·事定（Multi-function Room）] 2023-05-06 14:10–14:55>
<Booking [甘棠社区-102春·事定（Multi-function Room）] 2023-05-07 15:10–15:55>
……
```

### 🎨图形终端 TUI

目前还在早期测试阶段，仅仅能用而已。支持查询、搜索、预约。

```shell
$ pipx install bitroom[tui]
```

![RoomApp](https://github.com/YDX-2147483647/bitroom/assets/73375426/3ad4e0fd-dfb5-43ad-a07d-70b70b6242fa)

![BookScene](https://github.com/YDX-2147483647/bitroom/assets/73375426/18a824ce-f963-4f30-b0cb-b26a0f1583b2)

## ⚙️ 配置

（仅用于 CLI、TUI）

编辑`config.toml`，写入学号、密码，用于登录“统一身份认证”。

```toml
# 仅作示例，非真实信息
username = "1120771210"
password = "cyberpunk"
```

配置文件的位置遵循各操作系统惯例，可通过`bitroom config-paths`列出。另外，您也可用环境变量`$BITROOM_CONFIG_PATH`指定位置。

## 🌟 致谢

- [YoungKlaus/BIT_Auto_Leave: 北京理工大学自动请假](https://github.com/YoungKlaus/BIT_Auto_Leave/)
- [BITNP/bitsrun: 北京理工大学 10.0.0.55 校园网登录登出的 Python 实现](https://github.com/BITNP/bitsrun)
