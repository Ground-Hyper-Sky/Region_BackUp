import os
import time
import shutil
import datetime
import codecs
import json
import re

from mcdreforged.api.all import *
from region_backup.json_message import Message
from region_backup.config import rb_info, rb_config

Prefix = '!!rb'
# 默认的插件配置文件
cfg = rb_config.get_default().serialize()
# 默认的备份总文件夹
backup_path = "./rb_multi"
# 默认的备份文件夹位置
slot_path = "./rb_multi/slot{0}"
# 默认的overwrite文件夹位置
overwrite_path = f"{backup_path}/overwrite"
# 默认的服务端存档位置
world_path = "./server/world"
# 地狱，末地世界区域文件位置
dim_dict = {"the_nether": "DIM-1", "the_end": "DIM1"}
# 维度对应表
dim_list = {0: "overworld", 1: "the_end", -1: "the_nether"}
# 单维度完整备份列表
dim_folder = ["data", "poi", "entities", "region"]
# 全局分享列表
data_list = []
# 用户
user = None
# 备份状态符
backup_state = None
# 槽位默认数量
slot = 5
# 回档状态符
back_state = None
# 回档槽位
back_slot = None
# 超时
time_out = 5

help_msg = '''
------ {1} {2} ------
一个以区域为单位的§a备份回档§a插件
§3作者：FRUITS_CANDY
§d【格式说明】
#sc=!!rb<>st=点击运行指令#§7{0} §a§l[▷] §e显示帮助信息
#sc=!!rb make<>st=点击运行指令#§7{0} make §b<区块半径> <注释> §a§l[▷] §e以玩家所在区块为中心，备份边长为2倍半径+1的区块所在区域
#sc=!!rb dim_make<>st=点击运行指令#§7{0} dim_make §b<维度:0主世界,-1地狱,1末地> <注释> §a§l[▷] §e备份给定维度的所有区域,维度间用,做区分 §a例 0 或 0,-1
#sc=!!rb pos_make<>st=点击运行指令#§7{0} pos_make §b<x1坐标> <z1坐标> <x2坐标> <z2坐标> <维度:格式见上条指令> <注释> §a§l[▷] §e给定两个坐标点，备份以两坐标点对应的区域坐标为顶点形成的矩形区域
#sc=!!rb back<>st=点击运行指令#§7{0} back §b<槽位> §a§l[▷] §e回档指定槽位所对应的区域
#sc=!!rb restore<>st=点击运行指令#§7{0} restore §b<槽位> §a§l[▷] §e使存档还原到回档前状态
#sc=!!rb del<>st=点击运行指令#§7{0} del §b<槽位> §a§l[▷] §e删除某槽位
#sc=!!rb confirm<>st=点击运行指令#§7{0} confirm §a§l[▷] §e再次确认是否回档
#sc=!!rb abort<>st=点击运行指令#§7{0} abort §a§l[▷] §e在任何时候键入此指令可中断回档
#sc=!!rb list<>st=点击运行指令#§7{0} list §a§l[▷] §e显示各槽位的存档信息
#sc=!!rb reload<>st=点击运行指令#§7{0} reload §a§l[▷] §e重载插件
'''.format(Prefix, "Region BackUp", "1.6.1")


def print_help_msg(source: CommandSource):
    source.reply(Message.get_json_str(help_msg))
    rb_list(source)


@new_thread("rb_make")
def rb_make(source: InfoCommandSource, dic: dict):
    global backup_state, user
    try:
        if not source.get_info().is_player:
            source.reply("§c§l该指令只能由玩家输入!")
            return
        if backup_state is None:
            backup_state = False

            if "cmt" not in dic:
                dic["cmt"] = "§7空"

            r = int(dic["r"])

            if r < 0:
                source.reply("§c备份半径应为大于等于0的整数!")
                backup_state = None
                return

            source.get_server().broadcast("[RBU] §a备份§f中...请稍等")

            get_user_info(source)

            t = time.time()
            while len(data_list) < 4:
                if time.time() - t > time_out:
                    source.get_server().broadcast("[RBU] §c备份§f超时,已取消备份")
                    source.get_server().execute("save-on")
                    backup_state = None
                    user = None
                    return
                time.sleep(0.01)

            data = data_list.copy()
            data_list.clear()
            backup_pos = get_backup_pos(r, int(data[2][0] // 16), int(data[2][2] // 16))
            data[0] = source.get_info().player
            data[1] = source.get_info().content

            # 保存游戏
            source.get_server().execute("save-off")
            t1 = time.time()
            while backup_state != 1:
                if time.time() - t1 > time_out:
                    source.get_server().broadcast("[RBU] §c备份§f超时,已取消备份")
                    source.get_server().execute("save-on")
                    backup_state = None
                    user = None
                    return
                time.sleep(0.01)

            source.get_server().execute("save-all flush")
            t1 = time.time()
            while backup_state != 2:
                if time.time() - t1 > time_out:
                    source.get_server().broadcast("[RBU] §c备份§f超时,已取消备份")
                    source.get_server().execute("save-on")
                    backup_state = None
                    user = None
                    return
                time.sleep(0.01)

            user = None
            valid_pos = search_valid_pos(data[-1], backup_pos)

            rename_slot()

            copy_files(valid_pos, data[-1])

            make_info_file(dic["cmt"], data=data)

            t2 = time.time()
            source.get_server().broadcast(f"[RBU] §a备份§f完成，耗时§6{(t2 - t):.2f}§f秒")
            source.get_server().broadcast(
                f"[RBU] 日期: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}; 注释: {dic['cmt']}")

            source.get_server().execute("save-on")
            backup_state = None
            return

    except Exception as e:
        user = None
        backup_state = None
        source.reply(f"备份出错,错误信息:§c{e}")
        source.get_server().execute("save-on")
        return

    source.reply("§c§l备份正在进行,请不要重复备份!")


@new_thread("rb_pos_make")
def rb_pos_make(source: InfoCommandSource, dic: dict):
    global backup_state, user
    try:

        if backup_state is None:
            backup_state = False
            x1, z1, x2, z2 = dic["x1"], dic["z1"], dic["x2"], dic["z2"]

            if "cmt" not in dic:
                dic["cmt"] = "§7空"

            dim = int(dic["dim"])

            if dim not in dim_list:
                backup_state = None
                source.reply("§c维度输入错误")
                return

            dim = dim_list[dim]

            source.get_server().broadcast("[RBU] §a备份§f中...请稍等")

            backup_pos = get_backup_pos(pos_list=[(int(x1 // 512), int(x2 // 512)), (int(z1 // 512), int(z2 // 512))])
            user = source.get_info().is_user
            # 保存游戏
            source.get_server().execute("save-off")
            t1 = time.time()
            while backup_state != 1:
                if time.time() - t1 > time_out:
                    source.get_server().broadcast("[RBU] §c备份§f超时,已取消备份")
                    source.get_server().execute("save-on")
                    backup_state = None
                    user = None
                    return
                time.sleep(0.01)

            source.get_server().execute("save-all flush")
            t1 = time.time()
            while backup_state != 2:
                if time.time() - t1 > time_out:
                    source.get_server().broadcast("[RBU] §c备份§f超时,已取消备份")
                    source.get_server().execute("save-on")
                    backup_state = None
                    user = None
                    return
                time.sleep(0.01)

            user = None
            valid_pos = search_valid_pos(dim, backup_pos)

            if all(not v for v in valid_pos.values()):
                backup_state = None
                source.reply("§c本次备份无效,根据输入的坐标,未找到对应的区域")
                source.get_server().execute("save-on")

            rename_slot()

            copy_files(valid_pos, dim)

            make_info_file(dic["cmt"], backup_dim=dim,
                           user_=source.get_info().player if source.get_info().player else "from_console",
                           cmd=source.get_info().content
                           )

            t2 = time.time()
            source.get_server().broadcast(f"[RBU] §a备份§f完成，耗时§6{(t2 - t1):.2f}§f秒")
            source.get_server().broadcast(
                f"[RBU] 日期: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}; 注释: {dic['cmt']}")

            source.get_server().execute("save-on")
            backup_state = None
            return

    except Exception as e:
        backup_state = None
        user = None
        source.reply(f"备份出错,错误信息:§c{e}")
        source.get_server().execute("save-on")
        return

    source.reply("§c§l备份正在进行,请不要重复备份!")


@new_thread("rb_dim_make")
def rb_dim_make(source: InfoCommandSource, dic: dict):
    global backup_state, user

    try:
        if backup_state is None:
            backup_state = False

            if "cmt" not in dic:
                dic["cmt"] = "§7空"

            dim = dic["dim"]

            res = re.findall(r'-\d+|\d+', dim)
            dim = [int(s) if s[0] != '-' else -int(s[1:]) for s in res]
            if len(dim) != len(set(dim)):
                backup_state = None
                source.reply("§c维度输入重复")
                return

            backup_list = []

            for i in dim:
                if i not in dim_list:
                    backup_state = None
                    source.reply("§c维度输入错误")
                    return
                backup_list.append(dim_list[i])

            source.get_server().broadcast("[RBU] §a备份§f中...请稍等")

            user = source.get_info().is_user
            # 保存游戏
            source.get_server().execute("save-off")
            t = time.time()
            while backup_state != 1:
                if time.time() - t > time_out:
                    source.get_server().broadcast("[RBU] §c备份§f超时,已取消备份")
                    source.get_server().execute("save-on")
                    backup_state = None
                    user = None
                    return
                time.sleep(0.01)

            source.get_server().execute("save-all flush")
            t1 = time.time()
            while backup_state != 2:
                if time.time() - t1 > time_out:
                    source.get_server().broadcast("[RBU] §c备份§f超时,已取消备份")
                    source.get_server().execute("save-on")
                    backup_state = None
                    user = None
                    return
                time.sleep(0.01)

            user = None

            rename_slot()

            dim_path = []

            for i in backup_list:
                if i in dim_dict:
                    dim_path.append(dim_dict[i])
                else:
                    for j in dim_folder:
                        dim_path.append(j)

            time.sleep(0.1)

            for i in dim_path:
                shutil.copytree(os.path.join(world_path, i), os.path.join(backup_path, "slot1", i))

            make_info_file(dic["cmt"], backup_dim=",".join(backup_list),
                           user_=source.get_info().player if source.get_info().player else "from_console",
                           cmd=source.get_info().content)

            t2 = time.time()
            source.get_server().broadcast(f"[RBU] §a备份§f完成，耗时§6{(t2 - t):.2f}§f秒")
            source.get_server().broadcast(
                f"[RBU] 日期: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}; 注释: {dic['cmt']}")

            source.get_server().execute("save-on")
            backup_state = None
            return

    except Exception as e:
        user = None
        backup_state = None
        source.reply(f"备份出错,错误信息:§c{e}")
        source.get_server().execute("save-on")
        return

    source.reply("§c§l备份正在进行,请不要重复备份!")


# 玩家信息类型有如下两种 坐标，即Pos 维度，即Dimension
@new_thread("user_info")
def get_user_info(source):
    global user, data_list

    user = source.get_info().player

    if user:

        source.get_server().execute(f"data get entity {user} Pos")
        source.get_server().execute(f"data get entity {user} Dimension")

        t1 = time.time()
        while len(data_list) < 2:
            if time.time() - t1 > time_out:
                return
            time.sleep(0.01)

        data_list.append([float(pos.strip('d')) for pos in data_list[0].strip("[]").split(',')])
        data_list.append(data_list[1].replace("minecraft:", "").strip('"'))


@new_thread("rb_back")
def rb_back(source: InfoCommandSource, dic: dict):
    global back_state, back_slot
    # 判断槽位非空

    if not dic:
        if source.get_info().content.split()[1] == "restore":
            dic["slot"] = "overwrite"
        else:
            dic["slot"] = 1

    path = slot_path.format(dic["slot"]) if isinstance(dic["slot"], int) else os.path.join(backup_path, dic["slot"])

    if not os.path.exists(os.path.join(path, "info.json")):
        source.reply("§c该槽位无info.json文件或槽位不存在,无法回档")
        return

    if not get_file_size(
            [os.path.join(path, f) for f in os.listdir(path) if
             os.path.isdir(os.path.join(path, f))])[-1]:
        source.reply("§c该槽位无区域文件,无法回档")
        return

    try:

        if back_state is None:

            back_state = 0
            # 等待确认
            with codecs.open(os.path.join(path, "info.json"), encoding="utf-8-sig") as fp:
                info = json.load(fp)
                t = info["time"]
                cmt = info["comment"]

            source.reply(
                Message.get_json_str("\n".join([f"[RBU] 准备将存档恢复至槽位§6{dic['slot']}§f，日期 {t}; 注释: {cmt}",
                                                "[RBU] 使用#sc=!!rb confirm<>st=点击确认#§7!!rb confirm "
                                                "§f确认§c回档§f，#sc=!!rb abort<>st=点击取消#§7!!rb abort §f取消"])))
            t1 = time.time()
            while not back_state:
                if time.time() - t1 > 10:
                    source.reply("§a回档超时,已取消本次回档")
                    back_state = None
                    return
                time.sleep(0.01)

            if back_state is True:
                source.reply("§a回档已取消")
                back_state = None
                return
            # 提示

            source.get_server().broadcast("§c服务器将于10秒后关闭回档!")
            for stop_time in range(1, 10):
                time.sleep(1)
                if back_state is True:
                    back_state = None
                    source.reply("§a回档已取消")
                    return
                source.get_server().broadcast(Message.get_json_str("\n".join(
                    [
                        f"§a服务器还有{10 - stop_time}秒关闭，输入#sc=!!rb abort<>st=终止回档#§c!!rb abort§f来停止回档到槽位§6{dic['slot']}"])))

            back_slot = dic["slot"]
            # 停止服务器
            source.get_server().stop()
            back_state = None
            return

    except Exception as e:
        back_state = back_slot = None
        source.reply(f"回档出错,错误信息:§c{e}")
        return

    source.reply("§c§l回档正在进行,请不要重复回档!")


def on_server_stop(server: PluginServerInterface, server_return_code: int):
    global back_slot

    try:
        if back_slot:
            if server_return_code != 0:
                back_slot = None
                server.logger.error("服务端关闭异常,回档终止")
                return

            server.logger.info("§a正在运行文件替换")

            if os.path.exists(overwrite_path) and back_slot != "overwrite":
                shutil.rmtree(overwrite_path)
                os.makedirs(overwrite_path)

            path_ = slot_path.format(back_slot) if isinstance(back_slot, int) else os.path.join(backup_path,
                                                                                                "overwrite")

            with codecs.open(os.path.join(path_, "info.json"), encoding="utf-8-sig") as fp:
                info = json.load(fp)
                dim = info["backup_dimension"]

            dim_path = []

            back_list = dim.split(",")

            for i in back_list:
                if i not in dim_list.values():
                    back_slot = None
                    server.logger.error("请检查info.json里的维度信息是否正确")
                    return

                if i in dim_dict:
                    dim_path.append(dim_dict[i])

                else:
                    for j in dim_folder:
                        dim_path.append(j)

            if info["command"].split()[1] == "dim_make":

                if back_slot != "overwrite":
                    for i in dim_path:
                        shutil.copytree(os.path.join(world_path, i), os.path.join(overwrite_path, i))
                        shutil.rmtree(os.path.join(world_path, i))
                        shutil.copytree(os.path.join(path_, i), os.path.join(world_path, i))
                    shutil.copy2(os.path.join(path_, "info.json"),
                                 os.path.join(overwrite_path, "info.json"))

                else:
                    for i in dim_path:
                        shutil.rmtree(os.path.join(world_path, i))
                        shutil.copytree(os.path.join(path_, i), os.path.join(world_path, i))

            else:

                lst = [i for i in os.listdir(os.path.join(path_)) if os.path.isdir(os.path.join(path_, i))]

                dim_name = dim_path[0] if dim_path[0] in dim_dict.values() else ""

                if back_slot != "overwrite":

                    for i in lst:
                        os.makedirs(overwrite_path + f"/{i}")

                    for backup_file in lst:
                        if get_file_size([os.path.join(path_, backup_file)])[-1]:
                            lst_ = os.listdir(os.path.join(path_, backup_file))
                            for i in lst_:
                                # 复制即将被替换的区域到overwrite
                                shutil.copy2(os.path.join(world_path,dim_name, backup_file, i),
                                             os.path.join(overwrite_path, backup_file, i))
                                # 将备份的区域对存档里对应的区域替换
                                shutil.copy2(os.path.join(path_, backup_file, i),
                                             os.path.join(world_path, dim_name, backup_file, i))
                            # 复制本次回档槽位的info文件到overwrite
                            shutil.copy2(os.path.join(path_, "info.json"),
                                         os.path.join(overwrite_path, "info.json"))

                else:
                    for backup_file in lst:
                        if get_file_size([os.path.join(path_, backup_file)])[-1]:
                            lst_ = os.listdir(os.path.join(path_, backup_file))
                            for i in lst_:
                                # 将备份的区域对存档里对应的区域替换
                                shutil.copy2(os.path.join(path_, backup_file, i),
                                             os.path.join(world_path, dim_name, backup_file, i))

            back_slot = None

            server.start()

    except Exception as e:
        back_slot = None
        server.logger.error(f"回档出错,错误信息:§c{e}")
        return


def rb_del(source: CommandSource, dic: dict):
    try:
        # 获取文件夹地址
        s = slot_path.format(dic['slot'])
        # 删除整个文件夹
        if os.path.exists(s):
            shutil.rmtree(s, ignore_errors=True)
            source.reply(f"§4§l槽位{dic['slot']}删除成功")
            return

        source.reply(f"§4§l槽位{dic['slot']}不存在")

    except Exception as e:
        for i in range(1, slot + 1):
            os.makedirs(slot_path.format(i), exist_ok=True)
        source.reply(f"删除备份时出错,错误信息:§c{e}")
        return


def rb_abort(source: CommandSource):
    global back_state
    # 当前操作备份信息
    if back_state is None:
        source.reply("没有什么可中断的")
        return
    back_state = True


def rb_confirm(source: CommandSource):
    global back_state
    if back_state is None:
        source.reply("没有什么可确认的")
        return
    back_state = 1


def rb_list(source: CommandSource):
    try:
        slot_list = [_slot for _slot in os.listdir(backup_path) if
                     _slot.startswith("slot") and os.path.isdir(backup_path + rf"/{_slot}")]

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
                msg = f"[槽位§6{s}§f] 空"
                msg_list.append(msg)

        if not total_size:
            msg_list.append("备份占用总空间: 无")

        else:
            msg_list.append(f"备份占用总空间: §a{convert_bytes(total_size)}")

        source.reply(Message.get_json_str("\n".join(msg_list)))

    except Exception as e:
        source.reply(f"显示备份列表出错,错误信息:§c{e}")
        return


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
        source.reply(f"重载插件失败: §c§l{e}")


def on_unload(server: PluginServerInterface):
    global user, back_state, backup_state, back_slot
    user = backup_state = back_state = back_slot = None


def get_backup_pos(r=None, x=None, z=None, pos_list=None):
    backup_pos = []

    if not pos_list:
        return get_backup_pos(pos_list=[((x - r) // 32, (x + r) // 32), ((z + r) // 32, (z - r) // 32)])

    left = min(pos_list[0])
    right = max(pos_list[0])
    top = max(pos_list[-1])
    bottom = min(pos_list[-1])

    for x in range(left, right + 1):
        for z in range(bottom, top + 1):
            backup_pos.append((x, z))

    return backup_pos


def check_folder():
    if not os.path.exists("./config/Region_BackUp.json"):
        with codecs.open("./config/Region_BackUp.json", "w", encoding="utf-8-sig") as fp:
            json.dump(cfg, fp, ensure_ascii=False, indent=4)

    os.makedirs(backup_path, exist_ok=True)


def make_info_file(cmt, data=None, backup_dim=None, user_=None, cmd=None):
    file_path = os.path.join(slot_path.format(1), "info.json")

    info = rb_info.get_default().serialize()
    info["time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info["backup_dimension"] = data[-1] if not backup_dim else backup_dim
    info["user_dimension"] = data[-1] if not backup_dim else "无"
    info["user"] = data[0] if not user_ else user_
    info["user_pos"] = ",".join(str(pos) for pos in data[2]) if not user_ else "无"
    info["command"] = data[1] if not cmd else cmd
    info["comment"] = cmt

    with codecs.open(file_path, "w", encoding="utf-8-sig") as fp:
        json.dump(info, fp, ensure_ascii=False, indent=4)


def rename_slot():
    try:
        shutil.rmtree(slot_path.format(slot), ignore_errors=True)
        if slot > 1:
            for i in range(slot - 1, 0, -1):
                os.rename(slot_path.format(i), slot_path.format(i + 1))

        os.makedirs(slot_path.format(1))

    except:
        for i in range(1, slot + 1):
            os.makedirs(slot_path.format(i), exist_ok=True)


def copy_files(valid_pos, data):

    if data in dim_dict:
        path = os.path.join(world_path, dim_dict[data])

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

    if data in dim_dict:
        path = os.path.join(world_path, dim_dict[data])

    else:
        path = world_path

    for folder, positions in valid_pos.items():
        for pos in backup_pos:
            x, z = pos
            file = os.path.join(path, folder, f"r.{x}.{z}.mca")

            if os.path.exists(file):
                positions.append(pos)

    return valid_pos


def on_info(server: PluginServerInterface, info: Info):
    global backup_state
    if user:

        if info.content.startswith(f"{user} has the following entity data: ") and info.is_from_server:
            data_list.append(info.content.split(sep="entity data: ")[-1])
            return

        if info.content.startswith("Saved the game") and info.is_from_server:
            backup_state = 2
            return

        if info.content.startswith("Automatic saving is now disabled") and info.is_from_server:
            backup_state = 1
            return


def on_load(server: PluginServerInterface, old):
    global cfg, backup_path, slot_path, world_path, slot

    check_folder()

    for i in range(1, slot + 1):
        os.makedirs(slot_path.format(i), exist_ok=True)

    with codecs.open("./config/Region_BackUp.json", encoding="utf-8-sig") as fp:
        cfg = json.load(fp)

    backup_path = cfg["backup_path"]
    world_path = cfg["world_path"]
    slot_path = backup_path + "/slot{0}"
    slot = cfg["slot"]

    level_dict = cfg["minimum_permission_level"]

    require = Requirements()

    server.register_help_message('!!rb', '查看与区域备份有关的指令')

    builder = SimpleCommandBuilder()

    builder.command("!!rb", print_help_msg)
    builder.command("!!rb make <r> <cmt>", rb_make)
    builder.command("!!rb make <r>", rb_make)
    builder.command("!!rb dim_make <dim> <cmt>", rb_dim_make)
    builder.command("!!rb dim_make <dim>", rb_dim_make)
    builder.command("!!rb pos_make <x1> <z1> <x2> <z2> <dim> <cmt>", rb_pos_make)
    builder.command("!!rb pos_make <x1> <z1> <x2> <z2> <dim>", rb_pos_make)
    builder.command("!!rb back <slot>", rb_back)
    builder.command("!!rb back", rb_back)
    builder.command("!!rb restore", rb_back)
    builder.command("!!rb confirm", rb_confirm)
    builder.command("!!rb del <slot>", rb_del)
    builder.command("!!rb abort", rb_abort)
    builder.command("!!rb list", rb_list)
    builder.command("!!rb reload", rb_reload)

    builder.arg("x1", Number)
    builder.arg("z1", Number)
    builder.arg("x2", Number)
    builder.arg("z2", Number)
    builder.arg("dim", Text)
    builder.arg("r", Integer)
    builder.arg("cmt", GreedyText)
    builder.arg("slot", Integer)

    command_literals = ["make", "pos_make", "dim_make", "back", "restore", "confirm", "del", "abort", "list", "reload"]

    for literal in command_literals:
        permission = level_dict[literal]
        builder.literal(literal).requires(require.has_permission(permission),
                                          failure_message_getter=lambda err: "你没有运行该指令的权限")

    builder.register(server)
