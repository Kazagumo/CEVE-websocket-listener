from asyncio.windows_events import NULL
from pydantic.types import NoneBytes
import websockets
import json
import asyncio
import pickle
import base64
import functools
from pydantic import BaseModel

class kmtemplate(BaseModel):
    "作为筛选模板使用"
    
    
    char_id: int = None
    char_name: str = None
    ship: str = None
    ship_id: int = None
    group: str = None
    corp_id: int = None
    corp_name: int = None
    alli_id: int = None
    alli_name: str = None
    finalchar_id: int = None
    finalchar_name: str = None
    finalcorp_id: int = None
    finalcorp_name: str = None
    finalalli_id: int = None
    finalalli_name: str = None
    region: str = None
    system: str = None
    isk: float = None
    
    
        
    

    
class kminfo(kmtemplate):
    "用于查询km信息的工具"
    
    sec: float = None
    time: str = None
    killid: int = None
    
    @property
    def getlink(self):
        "拼接字符串,将killid便乘链接"
        
        return "https://kb.ceve-market.org/kill/"+str(self.killid)
    
    def load(self,dat: dict):
        "从已解析的websocket下发json载入km信息"
        
        self.killid = dat["killID"] #击杀报告id
        self.char_id = dat["char_id"] #角色id
        self.char_name = dat["char_name"] #角色名称
        self.ship = dat["ship"] #舰船名称
        self.ship_id = dat["ship_id"] #舰船id
        self.group = dat["group"] #舰船级别
        self.corp_id = dat["corp_id"] #公司id
        self.corp_name = dat["corp_name"] #公司名称
        self.alli_id = dat["alli_id"] #联盟id
        self.alli_name = dat["alli_name"] #联盟名称
        self.finalchar_id = dat["finalchar_id"] #最后一击角色id
        self.finalchar_name = dat["finalchar_name"] #最后一击角色名称
        self.finalcorp_id = dat["finalcorp_id"] #最后一击公司id
        self.finalcorp_name = dat["finalcorp_name"] #最后一击公司名称
        self.finalalli_id = dat["finalalli_id"] #最后一击联盟id
        self.finalalli_name = dat["finalalli_name"] #最后一击联盟名称
        self.region = dat["region"]
        self.system = dat["system"]
        self.sec = dat["sec"]
        self.time = dat["time"]
        self.isk = dat["isk"]
        
    def isincluded(self,spectemp: kmtemplate):
        "判断该km中是否存在与模板匹配的内容"
        
        if str(self.char_id) != str(spectemp.char_id) and spectemp.char_id != None:
            return False
        elif self.char_name != spectemp.char_name and spectemp.char_name != None:
            return False
        elif self.ship != spectemp.ship and spectemp.ship != None:
            return False
        elif str(self.ship_id) != str(spectemp.ship_id) and spectemp.ship_id != None:
            return False
        elif self.group != spectemp.group and spectemp.group != None:
            return False
        elif str(self.corp_id) != str(spectemp.corp_id) and spectemp.corp_id != None:
            return False
        elif self.corp_name != spectemp.corp_name and spectemp.corp_name != None:
            return False
        elif str(self.alli_id) != str(spectemp.alli_id) and spectemp.alli_id != None:
            return False
        elif self.alli_name != spectemp.alli_name and spectemp.alli_name != None:
            return False
        elif str(self.finalchar_id) != str(spectemp.finalchar_id) and spectemp.finalchar_id != None:
            return False
        elif self.finalchar_name != spectemp.finalchar_name and spectemp.finalchar_name != None:
            return False
        elif str(self.finalcorp_id) != str(spectemp.finalcorp_id) and spectemp.finalcorp_id != None:
            return False
        elif self.finalcorp_name != spectemp.finalcorp_name and spectemp.finalcorp_name != None:
            return False
        elif self.region != spectemp.region and spectemp.region != None:
            return False
        elif self.system != spectemp.system and spectemp.system != None:
            return False
        try:
            if float(self.isk) < float(spectemp.isk):
                return False
        except TypeError:
            if spectemp.isk != None:
                return False
        return True
        
        
        
        
cccc = 0
        
    

class kmclient(object):
    """
    从websocket持续拉取信息
    """
    
    def __init__(self):
        self.uri="wss://www.ceve-market.org/ws/cnkbnew?subscribe-broadcast"
        self.loop = asyncio.get_event_loop()
        self.state = 0
        self.__handlers = {}
        
    def connect(self, return_coroutine: bool = False):
        
        self.state = 1
        if return_coroutine:
            self.__is_single_room = False
            return self.__bootstrapper()
        else:
            self.__is_single_room = True
            asyncio.get_event_loop().run_until_complete(self.__bootstrapper())
            
    async def __bootstrapper(self):
        while self.state == 1:
            await self.__main()
    
    async def __main(self):
        try:
            while 1:
                async with websockets.connect(self.uri) as ws:
                    self.__ws = ws
                    await self.__loop()
        except websockets.ConnectionClosedError:
            return
    
    async def __loop(self):
        while True:
            data = pickle.loads(base64.b64decode(await self.__recv()))
            print(f"收到km,id{data.killid}")
            for handler in self.__handlers:
                if data.isincluded(pickle.loads(base64.b64decode(handler))):
                    asyncio.create_task(self.__run_as_asynchronous_func(self.__handlers[handler], data))
                    break
                
    async def __recv(self):
        raw_data = await self.__ws.recv()
        data = await self.__parse(raw_data)
        return data
    
    @staticmethod
    async def __run_as_asynchronous_func(func, *args):

        if asyncio.iscoroutinefunction(func):
            await func(*args)
        else:
            func(*args)

    def add_event_handler(self, key: kmtemplate, func):
        
        if not callable(func):
            raise TypeError("object is not callable")
        key = base64.b64encode(pickle.dumps(key)).decode(encoding="ascii")
        if key not in self.__handlers:
            self.__handlers[key] = func


            
            
    async def __parse(self ,raw: str) -> kminfo:
        newkm = kminfo()
        newkm.load(json.loads(raw))
        newkm = base64.b64encode(pickle.dumps(newkm)).decode(encoding="ascii")
        return newkm
    
    
    def on(self, key: kmtemplate):
        key = base64.b64encode(pickle.dumps(key)).decode(encoding="ascii")
        def decoration(func):
            if key not in self.__handlers:
                self.__handlers[key] = func

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                func(*args, **kwargs)
            return wrapper
        return decoration
    
    def disconnect(self):
        self.state = 0
        asyncio.gather(self.__ws.close())
        
        
    
            