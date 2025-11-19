# `luainstaller`: Python库, 开箱即用的`.lua`打包二进制, 包括依赖分析引擎  

***[English](./README.md)***  

> `luainstaller`开源于[GitHub](https://github.com/Water-Run/luainstallers/tree/main/luainstaller), 遵循`LGPL`协议, 是[luainstallers](https://github.com/Water-Run/luainstallers/tree/main)工具集的成员  

`luainstaller`是一个开源的**Python库**, 封装了预编译的[luastatic](https://github.com/ers35/luastatic/tree/master), 实现了依赖分析引擎, 提供了**一键式的将`.lua`打包为可执行文件的能力**.  

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
3. 根据依赖列表调用配置的二进制`luastatic`进行编译  

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

> 在这种情况下, 应当禁用自动依赖分析, 改用手动添加所需依赖.  

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

这将输出使用帮助.  

##### 获取可用的预编译脚本  

```bash
luainstaller binaries [-match 匹配的名称]
```

这将输出预编译的, 可用的二进制, 以`平台和位数_lua版本`组成, 以及默认的版本(`5.4.8`).  
例如, `winarm64_515`代表输出适用于Windows ARM 64位平台, 使用`lua 5.1.5`.  
默认情况下, 输出和当前平台环境一致的所有可用版本.  

参数说明:  

- `match`: 匹配名称的正则表达式  

#### 获取日志  

```bash
luainstaller logs [-limit 限制数] [-order {desc | asc}]
```

这将输出`luainstaller`存储的操作日志, 默认以操作时间倒序, 限制100条.  
日志系统使用[SimpSave](https://github.com/Water-Run/SimpSave).  

参数说明:  

- `limit`: 限制的输出数目, 大于0的整数  
- `order`: 按时间顺序(`asc`)/倒序`desc`  

#### 依赖分析  

```bash
luainstaller analyze 入口脚本 [-max 最大依赖数]
```

这将执行依赖分析, 输出分析列表.  
默认情况下, 分析至多36个依赖.  

参数说明:  

- `max`: 限制的最大依赖树, 大于0的整数  

#### 执行编译  

```bash
luainstaller 入口脚本 [-require <依赖的.lua脚本>] [-max 最大依赖数] [-binary <对应的lua版本>] [-output <输出的二进制路径>] [--manual] [--detail]
```

这将执行编译.  

参数说明:  

- `入口脚本`: 对应的入口脚本, 依赖分析的起点  
- `require`: 依赖的脚本, 如果对应脚本已由分析引擎自动分析到, 将跳过. 多个使用`,`隔开  
- `max`: 限制的最大依赖树, 大于0的整数. 默认情况下, 至多分析36个  
- `binary`: 选取指定的二进制版本, 可见于`luainstaller binaries`指令. 默认使用和当前平台一致的`lua 5.4.8`  
- `output`: 指定输出的二进制路径, 默认为在当前目录下和`.lua`同名的可执行文件, 在`Windows`平台上自动添加`.exe`后缀  
- `manual`: 不进行依赖分析, 直接编译入口脚本, 除非使用`-require`强制指定  
- `detail`: 详细的运行输出  

*示例:*  

```bash
luainstaller hello_world.lua
```

将`hello_world.lua`编译为同目录下的可执行文件`hello_world`(Linux)或`hello_world.exe`(Linux), 使用和系统相同位数的`lua 5.4.8`.  

```bash
luainstaller a.lua -require b.lua, c.lua --manual
```

将`a.lua`和依赖`b.lua`, `c.lua`一同打包为二进制, 不进行自动依赖分析, 此时行为和直接使用`luastatic`完全一致.  

```bash
luainstaller test.lua -binary lin32_515 -max 100 -output ../myProgram --detail
```

将`test.lua`使用`linux 32位`, `lua 5.1.5`打包, 设置至多分析至100个依赖项, 至上级目录下的`myProgram`二进制中, 并显示详尽的编译信息.  
