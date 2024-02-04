# Region_BackUp
一个以区域为单位备份或回档的MCDR插件
> [!TIP]
> 如果您想为这个项目作贡献，请直接发送PR，而不是创建issue :)
需要 `v2.6.0` 以上的 [MCDReforged](https://github.com/Fallen-Breath/MCDReforged)
## 命令格式说明

`!!rb` 显示帮助信息

`!!rb make <区块半径> <注释>` 以玩家所在区块为中心，备份边长为2倍半径+1的区块所在区域

`!!rb pos_make <x1坐标> <z1坐标> <x2坐标> <z2坐标> <维度> <注释>` 给定两个坐标点，备份以两坐标点对应的区域坐标为顶点形成的矩形区域

`!!rb back [<slot>]` 回档指定槽位所对应的区域

`!!rb del <slot>` 删除某槽位

`!!rb confirm` 再次确认是否回档

`!!rb abort` 在任何时候键入此指令可中断回档

`!!rb list` 显示各槽位的存档信息

`!!rb reload` 重载插件

## 配置文件选项说明

配置文件为 `config/region_backup.json`。它会在第一次运行时自动生成

### backup_path
默认值：`./rb_multi`
存储备份文件的路径

### word_path
默认值：`./server/world/`
服务器存档的路径

### minimum_permission_level
默认值：`{
        "make": 1,
        "pos_make": 1,
        "back": 2,
        "del": 2,
        "confirm": 1,
        "abort": 1,
        "reload": 2,
        "list": 0
    }`
一个字典，代表使用不同类型指令需要权限等级。数值含义见[此处](https://mcdreforged.readthedocs.io/zh_CN/latest/permission.html)

把所有数值设置成 `0` 以让所有人均可操作
