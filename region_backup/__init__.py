#                       _oo0oo_
#                      o8888888o
#                      88" . "88
#                      (| -_- |)
#                      0\  =  /0
#                    ___/`---'\___
#                  .' \\|     |// '.
#                 / \\|||  :  |||// \
#                / _||||| -:- |||||- \
#               |   | \\\  - /// |   |
#               | \_|  ''\---/''  |_/ |
#               \  .-\__  '-'  ___/-. /
#             ___'. .'  /--.--\  `. .'___
#          ."" '<  `.___\_<|>_/___.' >' "".
#         | | :  `- \`.;`\ _ /`;.`/ - ` : | |
#         \  \ `_.   \_ __\ /__ _/   .-` /  /
#     =====`-.____`.___ \_____/___.-`___.-'=====
#                       `=---='
#
#
#     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#           佛祖保佑       永不宕机     永无BUG
#
#       佛曰:
#               写字楼里写字间，写字间里程序员；
#               程序人员写程序，又拿程序换酒钱。
#               酒醒只在网上坐，酒醉还来网下眠；
#               酒醉酒醒日复日，网上网下年复年。
#               但愿老死电脑间，不愿鞠躬老板前；
#               奔驰宝马贵者趣，公交自行程序员。
#               别人笑我忒疯癫，我笑自己命太贱；
#               不见满街漂亮妹，哪个归得程序员？
#
import os
import time
import shutil
import datetime
import codecs
import json

from mcdreforged.api.all import *
from region_backup.json_message import Message
from region_backup.edit_json import Edit_Read as edit
from region_backup.config import rb_info, rb_config

Prefix = '!!rb'
# 默认的插件配置文件
cfg = rb_config.get_default().serialize()
# 默认的备份总文件夹
backup_path = "./rb_multi"
# 默认的备份文件夹位置
slot_path = "./rb_multi/slot{0}"
# 默认的服务端存档位置
world_path = "./server/world"
# 地狱，末地世界区域文件位置
dim_dict = {"the_nether": "DIM-1", "the_end": "DIM1"}
# 全局分享列表
data_list = []
# 用户
user = None
# 备份状态符
backup_state = None
# 槽位数量
slot = 5
# 回档状态符
back_state = None
# 回档槽位
back_slot = None

help_msg = '''
------ {1} {2} ------
一个以区域为单位的§a备份回档§a插件
§3作者：FRUITS_CANDY
§d【格式说明】
#sc=!!rb<>st=点击运行指令#§7{0} §a§l[▷] §e显示帮助信息
#sc=!!rb make<>st=点击运行指令#§7{0} make §b<备份半径> <注释> §a§l[▷] §e以玩家为中心，备份边长为2倍半径+1的矩形区域
#sc=!!rb pos_make<>st=点击运行指令#§7{0} pos_make §b<x1坐标> <z1坐标> <x2坐标> <z2坐标> <维度> <注释> §a§l[▷] §e给定两个坐标点，备份以两坐标点对应的区域坐标为顶点形成的矩形区域
#sc=!!rb back<>st=点击运行指令#§7{0} back §b<槽位> §a§l[▷] §e回档指定槽位所对应的区域
#sc=!!rb del<>st=点击运行指令#§7{0} del §b<槽位> §a§l[▷] §e删除某槽位
#sc=!!rb confirm<>st=点击运行指令#§7{0} confirm §a§l[▷] §e再次确认是否回档
#sc=!!rb abort<>st=点击运行指令#§7{0} abort §a§l[▷] §e在任何时候键入此指令可中断回档
#sc=!!rb list<>st=点击运行指令#§7{0} list §a§l[▷] §e显示各槽位的存档信息
#sc=!!rb reload<>st=点击运行指令#§7{0} reload §a§l[▷] §e重载插件
'''.format(Prefix, "Region BackUp", "1.0.0")


def print_help_msg(source: CommandSource):
    source.reply(Message.get_json_str(help_msg))


@new_thread("rb_make")
def rb_make(source: InfoCommandSource, dic: dict):
    global backup_state
    if backup_state is None:
        text = dic["r_comment"]
        lst = text.split()

        r = int(lst[0])

        get_user_info(source)
        while len(data_list) < 4:
            time.sleep(0.01)

        data = data_list.copy()
        data_list.clear()
        backup_pos = get_backup_pos(r, int(data[2][0] // 512), int(data[2][2] // 512))
        data[0] = source.get_info().player
        data[1] = source.get_info().content

        # 保存游戏
        source.get_server().execute("save-off")
        while backup_state == 1:
            time.sleep(0.01)
        backup_state = None

        source.get_server().execute("save-all flush")
        while backup_state == 2:
            time.sleep(0.01)

        source.reply("正在备份")
        valid_pos = search_valid_pos(data, backup_pos)
        check_folder()

        rename_slot()

        copy_files(valid_pos, data)

        make_info_file(data)

        source.reply("备份完成")
        source.get_server().execute("save-on")
        backup_state = None


# 玩家信息类型有如下两种 坐标，即Pos 维度，即Dimension
@new_thread("user_info")
def get_user_info(source):
    global user, data_list
    user = source.get_info().player

    if user:

        source.get_server().execute(f"data get entity {user} Pos")
        source.get_server().execute(f"data get entity {user} Dimension")

        while len(data_list) < 2:
            time.sleep(0.01)

        data_list.append([float(pos.strip('d')) for pos in data_list[0].strip("[]").split(',')])
        data_list.append(data_list[1].strip('"minecraft:"'))
        user = None


def rb_position_make():
    pass


@new_thread("rb_back")
def rb_back(source: CommandSource, dic: dict):
    global back_state, back_slot
    # 判断槽位非空
    if not os.path.exists(os.path.join(slot_path.format(dic["slot"]), "info.json")):
        source.reply(f"该槽位为空不可回档")
        return

    # 等待确认
    source.reply("是否进行回档操作")
    while back_state is None:
        time.sleep(0.01)

    if back_state:
        back_state = None
        return
    # 提示
    source.reply("服务器将于10秒后关闭回档")
    for stop_time in range(1, 10):
        time.sleep(1)
        if back_state:
            back_state = None
            source.reply("回档已停止")
            return
        source.reply(f"还有{10 - stop_time}秒关闭,输入!!rb abort停止")
    back_state = None
    back_slot = dic["slot"]
    # 停止服务器
    source.get_server().stop()


def on_server_stop(server: PluginServerInterface, server_return_code: int):
    global back_slot
    extra_slot = f"{backup_path}/overwrite"
    if back_slot:
        server.logger.error(f"正在运行文件替换")
        if os.path.exists(extra_slot):
            shutil.rmtree(extra_slot)
        os.makedirs(extra_slot)
        os.makedirs(extra_slot + "/entities")
        os.makedirs(extra_slot + "/region")
        os.makedirs(extra_slot + "/poi")

        # 打开压缩文件

        with codecs.open(os.path.join(slot_path.format(back_slot), "info.json"), encoding="utf-8-sig") as fp:
            info = json.load(fp)
            dim = info["backup_dimension"]
            if dim in dim_dict:
                path = os.path.join(world_path, dim_dict[dim])

            else:
                path = world_path

        for backup_file in ["entities", "region", "poi"]:
            lst = os.listdir(os.path.join(slot_path.format(back_slot), backup_file))
            for i in lst:
                shutil.copy2(os.path.join(path, backup_file, i), os.path.join(extra_slot, backup_file, i))
                # os.remove(os.path.join(path, backup_file, i))
                shutil.copy2(os.path.join(slot_path.format(back_slot), backup_file, i),
                             os.path.join(path, backup_file, i))

        back_slot = None

        server.start()


def rb_del(source: CommandSource, dic: dict):
    # 获取文件夹地址
    slot = slot_path.format(dic['slot'])
    if bool(os.listdir(f"{slot}")):
        # 删除整个文件夹
        shutil.rmtree(slot)
        # 创建文件夹
        os.makedirs(slot)
        source.reply(f"§4§l槽位{dic['slot']}删除成功")
        return
    # 判断槽位是否存在
    source.reply(f"§4§l槽位{dic['slot']}不存在")


def rb_abort():
    global back_state
    # 当前操作备份信息
    back_state = True


def rb_confirm():
    global back_state
    back_state = False


def rb_list(source: CommandSource):
    slot_list = [_slot for _slot in os.listdir(backup_path) if _slot.startswith("slot") and os.path.isdir(backup_path + rf"/{_slot}")]

    if not slot_list:
        source.reply("没有槽位存在")
        return

    slots = sorted(slot_list, key=lambda x: int(x.replace("slot", "")))

    msg_list = ["§d【槽位信息】"]

    total_size = 0

    for i in slots:
        s = i.strip('slot')
        json_path = os.path.join(backup_path, i, "info.json")
        if os.path.exists(json_path):
            with codecs.open(json_path, "r", "utf-8-sig") as fp:

                info = json.load(fp)

                if info:
                    t = info["time"]
                    cmt = info["comment"]
                    dim = info['backup_dimension']
                    size = get_file_size([os.path.join(backup_path, i)])
                    total_size += size[-1]

                    msg = f"#st=备份维度:{dim}#[槽位§6{s}§f] #sc=!!rb back {s}<>st=回档至槽位§6{s}#§a[▷] #sc=!!rb " \
                          f"del {s}<>st=删除槽位§6{s}#§c[x] ##§a{size[0]} §f{t} 注释: {cmt}"

                    msg_list.append(msg)
        else:
            msg = f"[槽位{s}] 空"
            msg_list.append(msg)

    if not total_size:
        msg_list.append("备份占用总空间: 无")

    else:
        msg_list.append(f"备份占用总空间: §a{convert_bytes(total_size)}")

    source.reply(Message.get_json_str("\n".join(msg_list)))


def get_file_size(folder_list):
    total_size = 0
    for directory in folder_list:

        for dirpath, dirnames, filenames in os.walk(directory):

            for filename in filenames:

                file_path = os.path.join(dirpath, filename)
                # 确保文件存在
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)

    return convert_bytes(total_size), total_size


def convert_bytes(size_in_bytes):
    """将字节转换为更易读的单位"""
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f}{x}"
        size_in_bytes /= 1024.0


def rb_reload(source: CommandSource):
    try:
        source.get_server().reload_plugin("region_backup")
        source.reply("§a§l插件已重载")
    except Exception as e:
        source.reply(f"§c§l重载插件失败: {e}")


def get_chunk_pos(pos):
    return pos // 16


def get_region_pos(pos):
    return pos // 512


def get_backup_pos(r, x, z):
    backup_pos = []
    n = (2 * r + 1) // 2

    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            backup_pos.append((x + i, z + j))

    return backup_pos


def check_folder():
    if not os.path.exists("./config/Region_BackUp.json"):

        with codecs.open("./config/Region_BackUp.json", "w", encoding="utf-8-sig") as fp:
            json.dump(cfg, fp, ensure_ascii=False, indent=4)

    os.makedirs(backup_path, exist_ok=True)

    for i in range(1, slot + 1):
        os.makedirs(slot_path.format(i), exist_ok=True)


def make_info_file(data):
    file_path = os.path.join(slot_path.format(1), "info.json")

    info = rb_info.get_default().serialize()
    info["time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info["backup_dimension"] = data[-1]
    info["user_dimension"] = data[-1]
    info["user"] = data[0]
    info["user_pos"] = ",".join(str(pos) for pos in data[2])
    info["command"] = data[1]
    info["comment"] = data[1].split(maxsplit=3)[-1] if len(data[1].split(maxsplit=2)[-1].split()) > 1 else "§7空"

    with codecs.open(file_path, "w", encoding="utf-8-sig") as fp:
        json.dump(info, fp, ensure_ascii=False, indent=4)


def rename_slot():
    # move_dir()
    shutil.rmtree(slot_path.format(slot))
    if slot > 1:
        for i in range(slot - 1, 0, -1):
            os.rename(slot_path.format(i), slot_path.format(i + 1))

    os.makedirs(slot_path.format(1))


def copy_files(valid_pos, data):
    if data[-1] in dim_dict:
        path = os.path.join(world_path, dim_dict[data[-1]])

    else:
        path = world_path

    time.sleep(0.1)

    for folder, positions in valid_pos.items():
        # 获取坐标的横纵坐标值
        if not positions:
            continue

        os.makedirs(os.path.join(slot_path.format(1), f"{folder}"), exist_ok=True)
        for pos in positions:
            x, z = pos
            file_path = os.path.join(path, folder, f"r.{x}.{z}.mca")
            shutil.copy2(file_path, os.path.join(slot_path.format(1), folder, f"r.{x}.{z}.mca"))


def search_valid_pos(data, backup_pos):
    valid_pos = {"region": [], "poi": [], "entities": []}

    if data[-1] in dim_dict:
        path = os.path.join(world_path, dim_dict[data[-1]])

    else:
        path = world_path

    for folder, positions in valid_pos.items():
        for pos in backup_pos:
            x, z = pos
            file = os.path.join(path, folder, f"r.{x}.{z}.mca")

            if os.path.isfile(file):
                positions.append(pos)

    return valid_pos


def get_pos(info: Info, player):
    pass


def on_info(server: PluginServerInterface, info: Info):
    global backup_state
    if user:

        if info.content.startswith(f"{user} has the following entity data:") and info.is_from_server:
            data_list.append(info.content.split(sep="entity data: ")[-1])
            return

        if info.content.startswith("Saved the game") and info.is_from_server:
            backup_state = 2
            return

        if info.content.startswith("Automatic saving is now disabled") and info.is_from_server:
            backup_state = 1
            return


def move_dir():
    dic_dir = {}
    # 文件夹对应状态
    for item in [backup_dir for backup_dir in os.listdir(backup_path) if not backup_dir.isalpha()]:
        dic_dir[item] = bool(os.listdir(f"{backup_path}/{item}"))

    flag = []
    for file in dic_dir.keys():
        if dic_dir[file]:
            # 非空
            if bool(flag):
                os.rename(f"{backup_path}/{file}", f"{backup_path}/{flag[0]}")
                dic_dir[flag[0]] = True
                dic_dir[file] = False
                flag.append(file)
                flag.pop(0)
        else:
            # 空
            shutil.rmtree(f"{backup_path}/{file}")
            flag.append(file)

    for filename in flag:
        os.makedirs(f"{backup_path}/{filename}")


def on_load(server: PluginServerInterface, old):
    global cfg, backup_path, slot_path, world_path, slot
    server.register_help_message('!!rb', '查看与区域备份有关的指令')

    builder = SimpleCommandBuilder()

    builder.command("!!rb", print_help_msg)
    builder.command("!!rb make <r_comment>", rb_make)
    builder.command("!!rb pos_make <x1> <z1> <x2> <z2> <dim_comment>", rb_position_make)
    builder.command("!!rb back <slot>", rb_back)
    builder.command("!!rb confirm", rb_confirm)
    builder.command("!!rb del <slot>", rb_del)
    builder.command("!!rb abort", rb_abort)
    builder.command("!!rb list", rb_list)
    builder.command("!!rb reload", rb_reload)

    builder.arg("r_comment", GreedyText)
    builder.arg("x1", Number)
    builder.arg("z1", Number)
    builder.arg("x2", Number)
    builder.arg("z2", Number)
    builder.arg("dim_comment", Integer)
    builder.arg("slot", Integer)

    builder.register(server)

    check_folder()

    with codecs.open("./config/Region_BackUp.json", encoding="utf-8-sig") as fp:
        cfg = json.load(fp)

    backup_path = cfg["backup_path"]
    world_path = cfg["world_path"]
    slot_path = backup_path + "/slot{0}"
    slot = cfg["slot"]
