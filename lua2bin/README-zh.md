# `lua2bin`  

***[English](./README.md)***  

> `lua2bin`开源于[GitHub](https://github.com/Water-Run/luainstallers/tree/main/lua2bin), 遵循`LGPL`协议, 是[luainstallers](https://github.com/Water-Run/luainstallers)工具集的成员  

`lua2bin`是一个开源的**lua库**, 封装了预编译的[luastatic](https://github.com/ers35/luastatic/tree/master), 实现了依赖树分析引擎, 提供了**一键式的将`.lua`打包为可执行文件的能力**.  

`lua2bin`发布在[luarocks]()上, 使用`luarocks install lua2bin`即可安装. 提供了面向对象的接口, 非常简洁易懂.  

*示例代码:*  

```lua
lua2bin = require('lua2bin')

myProgram = lua2bin.instance(
    'myProgram.lua'
)

myProgram:compile()
```

```lua
lua2bin = require('lua2bin')

myProgram = lua2bin.instance(
    'myProgram.lua'
)

myProgram.analyze = false;
myProgram:require('require_1.lua')
myProgram.set(lua2bin.BINS.WIN32_50)

myProgram:build(
    'MyPath.exe'
)
```

## 参考  

以下为`lua2bin`提供的各方法, 枚举等的详细说明:  

### `BINS`: 所有可用的二进制版本  

`lua2bin.BINS`的一个字符串枚举, 包括所有可用的二进制版本:  

|枚举项名称|值|平台|架构|Lua版本|
|---|---|---|---|---|
|`WIN32_515`|`'WIN32_50'`|`Windows`|`X86`|`5.1.5`|

> 另可使用`lua2bin.allBins()`列出所有可用的预编译版本  

### `instance()`: 创建一个打包实例  

`lua2bin.instance()`方法作为构造函数, 创建打包实例.  
构造包括如下属性(按照位置顺序):  

|名称|类型|说明|可`nil`缺省|
|---|---|---|---|
|`lua_entry`|`string`, 合法的路径, 文件存在且以`.lua`为后缀|入口脚本|否|
|`bin_output`|`string`|输出的二进制, 合法的路径|是, 缺省为同名同目录(不含`.lua`后缀名)|

> 在构造完成后, 也可修改对应的属性, 名称和形参一致  

构造实例后, 可调用方法:  
