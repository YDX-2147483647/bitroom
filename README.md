# 🚩🏠 bitroom (Book an Incongruent Topological Room Or be Out of Mind)

BIT 场地预约查询接口。

## 🧪 例子

（要先克隆仓库，[`pdm install`](https://pdm.fming.dev/latest/reference/cli/#install)）

```shell
$ pdm run bitroom --help
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
$ pdm run bitroom show --help
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
$ pdm run bitroom show
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

## ⚙️ 配置

编辑`config.toml`，写入学号、密码，用于登录场地预约系统。

```toml
# 仅作示例，非真实信息
username = "1120771210"
password = "cyberpunk"
```

配置文件的位置遵循各操作系统惯例，可通过`bitroom config-paths`列出。另外，您也可用环境变量`$BITROOM_CONFIG_PATH`指定位置。

## 🌟 致谢

- [YoungKlaus/BIT_Auto_Leave: 北京理工大学自动请假](https://github.com/YoungKlaus/BIT_Auto_Leave/)
- [BITNP/bitsrun: 北京理工大学 10.0.0.55 校园网登录登出的 Python 实现](https://github.com/BITNP/bitsrun)
