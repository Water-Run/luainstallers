# `luainstaller`: Python库, 将`.lua`打包二进制, 包括依赖分析能力  

***[English](./README.md)***  

> `luainstaller`开源于[GitHub](https://github.com/Water-Run/luainstallers/tree/main/luainstaller), 遵循`LGPL`协议, 是[luainstallers](https://github.com/Water-Run/luainstallers/tree/main)工具集的成员  

`luainstaller`是一个开源的**Python库**, 封装了**将`.lua`打包为可执行文件**的能力. 包括:  

- 可选打包引擎: 使用`srlua`作为打包引擎时开箱即用  
- 实现了依赖分析引擎, 可以自动的进行依赖分析, 包括来自`luarocks`中的包  

`luainstaller`可以:  

- ***以命令行工具使用***  
- ***以图形化工具使用***  
- ***作为库引入到你的项目中***  

## 安装  

`luainstaller`发布在[pypi]()上, 使用`pip`进行安装:  

```bash
pip install luainstaller
```

安装完毕后, 在终端中运行:  

```bash
luainstaller
```

获取输出:  

```plaintext
luainstaller by WaterRun. Version 1.0.
Visit: https://github.com/Water-Run/luainstallers/tree/main/luainstaller :-)
```

即安装成功.  

## 上手教程  

`luainstaller`的工作流很简洁:  

1. 对入口脚本扫描, 递归, 构建依赖分析(如果自动依赖分析未被禁用)  
2. 合并手动配置的依赖脚本, 生成依赖列表  
3. 根据依赖列表调用打包引擎进行编译, 输出到指定目录  

如图示:  

```plaintext
test.lua <入口脚本>
 | {自动依赖分析}
 ├──> require("utils/log")
 │     └── utils/log.lua
 │           └── require("utils/time")
 │                 └── utils/time.lua       ==>    <依赖清单>
 ├──> require("core/init")                       [   
 │     ├── core/init.lua                         "utils/log.lua",
 │     ├── core/config.lua                       "utils/time.lua",
 │     └── core/db.lua                           "core/init.lua",
 └──(手动配置依赖)                                "core/config.lua",
       └── extra/plugin.lua                      "core/db.lua", 
                                                 "extra/plugin.lua"
                                                 ]                                     
                                          ↓
                       {调用对应版本的预编译luastatic编译命令}
win64_546 test.lua utils/log.lua utils/time.lua core/init.lua core/config.lua core/db.lua extra/plugin.lua -o test.exe
```

### 关于自动依赖分析  

`luainstaller`的自动依赖分析引擎会匹配以下形式的`requrie`语句:  

```lua
require '{pkg_name}'
require "{pkg_name}"
require('pkg_name')
require("pkg_name")
require([[pkg_name]])
```

此外的形式将导致报错, 包括动态依赖等.  

> 在这种情况下, 应当禁用自动依赖分析, 改用手动添加所需依赖  

### 关于可选引擎  

`luainstaller`支持可选打包引擎.  

- 默认使用[srlua](https://github.com/LuaDist/srlua), 一个经典, 简单的打包引擎. 封装预编译的版本, 实现开箱即用.  

- 可选[luastatic](https://github.com/ers35/luastatic)引擎, 能够编译为真正的二进制.  

> 使用`luastatic`引擎需要进行环境配置, 确保环境变量中存在:  
>> lua: [Lua官网](https://www.lua.org/), 包括包管理器`luarocks`  
>> luastatic: `luarocks install luastatic`  
>> gcc: `linux`上一般自带, `windows`上参考: [MinGW](https://github.com/niXman/mingw-builds-binaries)

### 作为图形化工具使用  

最简单的使用方式莫过于使用`GUI`了.  
`luainstaller`提供一个由`Tkinter`实现的图形界面. 在完成安装后, 在终端中输入:  

```bash
luainstaller-gui
```

即可启动.  

> GUI界面仅包含基础功能  

### 作为命令行工具使用  

`luainstaller`也可直接作为命令行工具使用. 直接在终端中输入:  

```bash
luainstaller
```

即可.  

> 或`luainstaller-cli`, 二者是等效的  

#### 指令集  

##### 获取帮助  

```bash
luainstaller help
```

##### 获取日志  

```bash
luainstaller logs [-limit 限制数] [-asc]
```

##### 依赖分析  

```bash
luainstaller analyze 入口脚本 [-max 最大依赖数]
```

##### 执行编译  

```bash
luainstaller build 入口脚本 [-require <依赖的.lua脚本>] [-max 最大依赖数] [-output <输出的二进制路径>] [--luastatic] [--manual] [--detail]
```

## 作为库使用  

`luainstaller`也可以作为库导入你的脚本中:  

```python
import luainstaller
```

并提供函数式的API.  

## API参考  

### `get_logs()`

获取日志  

```python
def get_logs(limit: int | None = None,
             _range: range | None = None,
             desc: bool = True) -> list[dict[str, Any]]:
    r"""
    返回luainstaller日志.
    :param limit: 返回数限制, None表示不限制
    :param _range: 返回范围限制, None表示不限制
    :param desc: 是否倒序返回
    :return list[dict[str, Any]]: 日志字典组成的列表
    """
```

示例:

```python
import luainstaller

log_1: dict = luainstaller.get_logs() # 以倒序获取全部日志
log_2: dict = luainstaller.get_logs(limit = 100, _range = range(128, 256), desc=False) # 以顺序获取最多一百条, 范围在128到256之间的日志
```

### `analyze()`

执行依赖分析（对应 CLI 的 `luainstaller analyze`）

```python
def analyze(entry: str,
            max_deps: int = 36) -> list[str]:
    r"""
    对入口脚本执行依赖分析.

    :param entry: 入口脚本路径
    :param max_deps: 最大递归依赖数, 默认36
    :return list[str]: 分析得到的依赖脚本路径列表
    """
```

示例:

```python
import luainstaller

deps_1: list = luainstaller.analyze("main.lua") # 依赖分析, 默认最多分析36个依赖
deps_2: list = luainstaller.analyze("main.lua", max_deps=112) # 执行依赖分析, 将最大依赖分析数量修改为112
```

### `build()`

执行编译（对应 CLI 的 `luainstaller build`）

```python
def build(entry: str,
          requires: list[str] | None = None,
          max_deps: int = 36,
          output: str | None = None,
          use_luastatic: bool = False,
          manual: bool = False,
          detail: bool = False,
          binary: str | None = None) -> str:
    r"""
    执行脚本编译.

    :param entry: 入口脚本
    :param requires: 手动指定依赖列表; 若为空则仅依赖自动分析
    :param max_deps: 最大依赖树分析数
    :param output: 输出二进制路径, None 使用默认规则
    :param use_luastatic: 是否使用luastatic作为打包引擎
    :param manual: 禁用自动依赖分析
    :param detail: 是否输出详细信息
    :param binary: 指定预编译luastatic二进制(如 'win64_546')
    :return str: 生成的可执行文件路径
    """
```

示例:

```python
import luainstaller

# 最简单的构建方式, 自动分析依赖并生成与脚本同名的可执行文件
luainstaller.build("hello.lua")

# 手动模式: 禁用自动依赖分析, 仅使用 requires 指定的依赖脚本进行编译
luainstaller.build("a.lua", requires=["b.lua", "c.lua"], manual=True)

# 高级构建示例:
# - 启用 luastatic 引擎
# - 指定使用预编译二进制 lin32_515 (linux 32bit + lua 5.1.5)
# - 设置最大依赖分析数为100
# - 输出二进制到 "bin/myProgram"
# - 启用详细输出
luainstaller.build(
    "test.lua",
    max_deps=100,
    output="bin/myProgram",
    use_luastatic=True,
    detail=True,
    binary="lin32_515"
)
```
