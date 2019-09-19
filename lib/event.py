from lib import global_var, WriteLog
import re
from project.function import add_item, set_item_amount, flush_status
import pygame

# 事件基本单元
class Event:
    """
    事件类型（cls）：
        control - 控制流 if while 等
        data - 数据操作
        show - 显示操作

    """
    def __init__(self):
        self.cls = '' # 类型： 逻辑/显示
        self.PlayerCon = global_var.get_value("PlayerCon")
        self.CurrentMap = global_var.get_value("CurrentMap")
        self.TEXTBOX = global_var.get_value("TEXTBOX")
        self.BlockDataReverse = global_var.get_value("BlockDataReverse")
        self.Music = global_var.get_value("Music")

    def get_event_flow_module(self):
        self.EVENTFLOW = global_var.get_value("EVENTFLOW")

    # 显示一段文字
    def text(self, event):
        # 正则匹配\t[.....]
        result = re.match("\\t\[\S*\]", event)
        if result is not None:
            header = result.group()
            event = event.lstrip(header)
            header = header.lstrip("\t[")
            header = header.rstrip("]")
            header = header.split(",")
            if len(header) == 1:
                name = header[0]
                event = name + "\n" + event
            if len(header) == 2:
                name = header[0]
                icon = header[1]
                # TODO: 显示icon
                event = name + "\n" + event
        self.TEXTBOX.show(event)

    # if条件判断
    def if_cond(self, event):
        condition = event["condition"]
        cond_is_reversed = False
        # 正则匹配!(......)
        result = re.match("!\(\S*\)", condition)
        if result is not None:
            cond_is_reversed = not cond_is_reversed
            condition = condition.lstrip("!(")
            condition = condition.rstrip(")")
        # 正则匹配(!......)
        result = re.match("\(!\S*\)", condition)
        if result is not None:
            cond_is_reversed = not cond_is_reversed
            condition = condition.lstrip("(!")
            condition = condition.rstrip(")")         
        cond_eval_result = condition in self.PlayerCon.var
        if cond_is_reversed:
            cond_eval_result = not cond_eval_result
        if cond_eval_result:
            self.EVENTFLOW.insert_action(event["true"])
        else:
            self.EVENTFLOW.insert_action(event["false"])

    # 设置玩家属性，道具数量，或者变量的值
    def set_value(self, event):
        event_type = event["type"]
        value_name = event["name"]
        value = int(event["value"])
        if "flag:" in value_name or "switch:" in value_name:
            # TODO: 独立开关需要进一步处理，否则无法识别不同事件的独立开关
            if event_type == "setValue":
                self.PlayerCon.var[value_name] = value
            elif event_type == "addValue":
                if value_name in self.PlayerCon.var:
                    self.PlayerCon.var[value_name] += value
                else:
                    self.PlayerCon.var[value_name] = value
        elif "item:" in value_name:
            value_name = value_name.lstrip("item:")
            if value_name in self.BlockDataReverse:
                map_obj_id = int(self.BlockDataReverse[value_name])
                if event_type == "setValue":
                    set_item_amount(map_obj_id, value)
                elif event_type == "addValue":
                    add_item(map_obj_id, value) 
            else:
                self.TEXTBOX.show(f"请检查{value_name}是否正确")
                print(f"请检查{value_name}是否正确")
        else:
            self.TEXTBOX.show(f"暂时无法解析：{event}")
            print(f"暂时无法解析：{event}")
        flush_status()

    # 打开全局商店
    def open_shop(self, event):
        shop_id = event["id"]
        chosen_shop = global_var.get_value(shop_id)
        chosen_shop.open()

    # 播放音效
    def play_sound(self, event):
        sound_name = event["name"]
        self.Music.play_SE(sound_name)

    # 开门
    def open_door(self, event):
        loc = event["loc"]
        x = loc[0]
        y = loc[1]
        if "floorId" in event:
            floor_id = event["floorId"]
        else:
            floor_id = self.CurrentMap.get_floor_id(self.PlayerCon.floor)
        self.CurrentMap.MAP_DATABASE[floor_id]["map"][y][x] = 0

    # 等待一段时间（单位是毫秒）
    def sleep(self, event):
        sleep_time = int(event["time"])
        pygame.time.wait(sleep_time)

class EventFlow:
    def __init__(self):
        self.data_list = []  # 当前在执行的事件列表
        self.auto = False  # 自动执行中
        self.wait_key = None  # 等待驱动的关键按钮
        self.PlayerCon = global_var.get_value("PlayerCon")
        self.CurrentMap = global_var.get_value("CurrentMap")
        self.TEXTBOX = global_var.get_value("TEXTBOX")

    def get_event_module(self):
        self.EVENT = global_var.get_value("EVENT")

    # 立即执行列表中的事件
    def do_action(self):
        self.data_list.pop(0)
        # TODO: 执行事件

    # 把事件放到当前队列的末尾
    def add_action(self, x, y, floor=None):
        lst = self.get_event_list(x, y)
        if type(lst) is not list:
            lst = [lst]
        self.data_list = self.data_list + lst

    # 插入一系列事件到当前的列表中
    def insert_action(self, lst):
        if type(lst) is not list:
            lst = [lst]
        self.data_list = lst + self.data_list

    def get_event_list(self, x, y, floor=None):
        if floor is None:
            floor = self.PlayerCon.floor
        if floor == self.PlayerCon.floor:
            flow = self.CurrentMap.get_event_flow(x, y, floor)
            if type(flow) is dict and len(flow) == 5:
                if "data" in flow:
                    flow = flow["data"]
            # self.CurrentMap.event_data.remove([x, y]) 这句不启用，因为事件可以反复触发，除非被隐藏
            return flow

    def do_event(self):
        if not self.PlayerCon.lock:
            event = self.data_list[0]
            WriteLog.debug(__name__, "当前执行事件：" + str(self.data_list[0]))
            self.data_list.pop(0)
            if type(event) is dict:
                event_type = event["type"]
                if event_type == "if":
                    self.EVENT.if_cond(event)
                elif event_type == "setValue" or event_type == "addValue":
                    self.EVENT.set_value(event)
                elif event_type == "openShop":
                    self.EVENT.open_shop(event)
                elif event_type == "openDoor":
                    self.EVENT.open_door(event)
                elif event_type == "playSound":
                    self.EVENT.play_sound(event)
                elif event_type == "sleep":
                    self.EVENT.sleep(event)
                else:
                    self.TEXTBOX.show(f"暂时无法解析：{event}")
                    print(f"暂时无法解析：{event}")
            elif type(event) is str:
                self.EVENT.text(event)
            else:
                self.TEXTBOX.show(f"暂时无法解析：{event}")
                print(f"暂时无法解析：{event}")

                        


        


