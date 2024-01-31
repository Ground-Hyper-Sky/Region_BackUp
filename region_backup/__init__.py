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
#----------------------------------------------------------------
import time
import os
import zipfile
import shutil
import codecs

from mcdreforged.api.all import *

from region_backup.json_message import Message
from region_backup.edit_json import Edit_Read as edit

Prefix = '!!rb'
dim_dict = {"the_nether": "DIM-1", "the_end": "DIM1"}
data_list = []
user = None
backup_state = None
server_path = "./server/world"
rb_multi = "./rb_multi"
slot = 5

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
        text = dic["r_des"]
        lst = text.split()

        if len(lst) == 1:
            try:
                r = int(lst[0])
                des = "空"

            except ValueError:
                source.reply("输入错误")
                return
        else:
            try:
                r = int(lst[0])
                des = text.split(maxsplit=1)[1]

            except ValueError:
                source.reply("输入错误")
                return

        get_user_info(source)
        while len(data_list) < 4:
            time.sleep(0.01)
        backup_pos = get_backup_pos(r, int(data_list[2][0] // 512), int(data_list[2][2] // 512))
        data = data_list.copy()
        data_list.clear()

        # 保存游戏
        source.get_server().execute("save-all")
        while backup_state == 1:
            time.sleep(0.01)
        backup_state = None

        source.get_server().execute("save-off")
        while backup_state == 2:
            time.sleep(0.01)

        valid_pos = search_valid_pos(data, backup_pos)
        check_folder()

        rename_slot()

        compress_files(valid_pos, data)

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


def rb_back():
    pass


def rb_confirm():
    pass


def rb_del():
    pass


def rb_abort():
    pass


def rb_list():
    pass


def rb_reload():
    pass


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


def check_folder(folder_path=None):
    if folder_path and not os.path.exists(folder_path):
        os.makedirs(folder_path)

    os.makedirs(rb_multi, exist_ok=True)

    for i in range(1, slot + 1):
        os.makedirs(os.path.join(rb_multi, f"slot{i}"), exist_ok=True)

def make_info_file():
    pass

def rename_slot():
    shutil.rmtree(os.path.join(rb_multi, f"slot{slot}"))
    if slot > 1:
        for i in range(slot - 1, 0, -1):
            os.rename(os.path.join(rb_multi, f"slot{i}"), os.path.join(rb_multi, f"slot{i + 1}"))

    os.makedirs(os.path.join(rb_multi, "slot1"))


def compress_files(valid_pos, data):
    if data[-1] in dim_dict:
        path = os.path.join(server_path, dim_dict[data[-1]])

    else:
        path = server_path

    for folder, positions in valid_pos.items():
        # 获取坐标的横纵坐标值
        if not positions:
            continue

        with zipfile.ZipFile(os.path.join(rb_multi, "slot1", f"{folder}.zip"), 'w', zipfile.ZIP_DEFLATED) as zipf:
            for pos in positions:
                x, z = pos

                file_path = os.path.join(path, folder, f"r.{x}.{z}.mca")

                zipf.write(file_path, arcname=f"r.{x}.{z}.mca")


def search_valid_pos(data, backup_pos):
    valid_pos = {"region": [], "poi": [], "entities": []}

    if data[-1] in dim_dict:
        path = os.path.join(server_path, dim_dict[data[-1]])

    else:
        path = server_path

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
    if not user:
        return

    if info.content.startswith(f"{user} has the following entity data:") and info.is_from_server:
        data_list.append(info.content.split(sep="entity data: ")[-1])
        return

    if info.content.startswith("Saved the game") and info.is_from_server:
        backup_state = 1

    if info.content.startswith("Automatic saving is now disabled") and info.is_from_server:
        backup_state = 2


def on_load(server: PluginServerInterface, old):
    server.register_help_message('!!rb', '查看与区域备份有关的指令')

    builder = SimpleCommandBuilder()

    builder.command("!!rb", print_help_msg)
    builder.command("!!rb make <r_des>", rb_make)
    builder.command("!!rb pos_make <x1> <z1> <x2> <z2> <dim_des>", rb_position_make)
    builder.command("!!rb back <slot>", rb_back)
    builder.command("!!rb confirm", rb_confirm)
    builder.command("!!rb del <slot>", rb_del)
    builder.command("!!rb abort", rb_abort)
    builder.command("!!rb list", rb_list)
    builder.command("!!rb reload", rb_reload)

    builder.arg("r_des", GreedyText)
    builder.arg("x1", Number)
    builder.arg("z1", Number)
    builder.arg("x2", Number)
    builder.arg("z2", Number)
    builder.arg("dim_des", Integer)
    builder.arg("slot", Integer)

    builder.register(server)

    check_folder()
