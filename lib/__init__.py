# 库文件初始化区 通用访问接口在这里（如CurrentMap） ! 注意导包顺序 很重要

from .map import MapGround
from sysconf import *
# 当前地图Ground 需要被初始化时添加到屏幕Ground中
CurrentMap = MapGround(13, 13, BLOCK_UNIT)


from .control import Player
# 角色控制/显示器
PlayerCon = Player()
