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
import json
import os
import codecs

from mcdreforged.api.all import *

Prefix = '!!rb'

help_msg = '''
------ {1} {2} ------
一个以区域为单位的§a备份回档§a插件
§3作者：FRUITS_CANDY,mc_doge_
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
'''.format(Prefix, "Auto execute", "1.0.0")


def print_help_msg():
    pass

def rb_make(source: CommandSource, dic: dict):
    pass

def rb_position_make():
    pass

def rb_back():
    pass

def rb_confirm():
    pass

def rb_del(source: CommandSource, dic: dict):
    #获取文件夹地址
    slot = backup_path.format(dic['slot'])
    #判断槽位是否存在
    if not os.path.exists(slot):
        source.reply(f"§4§l槽位{dic['slot']}不存在")
    else:
        #删除整个文件夹
        os.remove("slot")

def rb_abort():
    pass

def rb_list():
    pass

def rb_reload():
    pass

def on_load(server: PluginServerInterface, old):
    server.register_help_message('!!rb', '查看与区域备份有关的指令')

    builder = SimpleCommandBuilder()

    builder.command("!!rb",print_help_msg)
    builder.command("!!rb make <r_des>",rb_make)
    builder.command("!!rb pos_make <x1> <z1> <x2> <z2> <dim> <des>",rb_position_make)
    builder.command("!!rb back <slot>",rb_back)
    builder.command("!!rb confirm",rb_confirm)
    builder.command("!!rb del <slot>",rb_del)
    builder.command("!!rb abort",rb_abort)
    builder.command("!!rb list",rb_list)
    builder.command("!!rb reload",rb_reload)

    builder.arg("r_des",GreedyText)
    builder.arg("x1",Number)
    builder.arg("z1",Number)
    builder.arg("x2",Number)
    builder.arg("z2",Number)
    builder.arg("dim",Integer)
    builder.arg("slot",Integer)

    builder.register(server)
