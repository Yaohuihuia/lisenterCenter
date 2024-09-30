import socketio
class lisenter:
    def __init__(self,name,mangerUrl) -> None:
        '''
        子服务名称
        name: 当前服务的名称
        mangerUrl: 中心服务的url
        '''
        self.name=name
        self.mangerUrl=mangerUrl
        self.status=False
        self.sio = socketio.Client()
        self.ackId=1
        self.callbackMap={}
        self.managerData=[]
        self.sio.connect(self.mangerUrl)
        self.sio.emit('register',self.name)
        
        @self.sio.on('managerData')
        def managerData(data):
            self.managerData=data
            
        @self.sio.on('toRun')
        def toRun(data):
            for each in data["ackIds"]:
                self.callbackMap[each]["callback"](*data['args'],**data['kwargs'])
                  
    def addevent(self,eventName,info):
        '''
        添加事件
        eventName: 事件名
        info: 事件的描述，可以包含事件的触发场景和触发时会传入的参数
        '''
        self.sio.emit('addevent',{'eventName':eventName,'info':info})
    
    def emit(self,eventName,*args,**kwargs):
        '''
        触发事件
        eventName: 事件名
        '''
        self.sio.emit('emit',{'eventName':eventName,'args':args,'kwargs':kwargs})    
    
    def rmEvent(self,eventName):
        '''
        移除事件
        eventName: 事件名
        '''  
        self.sio.emit('rmEvent',eventName)
    
    
    def rmcallbackById(self,Id):
        if self.callbackMap.get(Id)["count"]==1:
            del self.callbackMap[Id]
        elif self.callbackMap.get(Id)["count"]>1:
            self.callbackMap[Id]["count"]-=1
    
    def on(self,serverName,eventName,callback):
        '''
        监听事件
        serverName: 监听事件的目标服务器名称
        eventName: 监听目标服务的事件名
        callback: 监听事件执行时的回调函数
        '''
        myackid=None
        for k,v in self.callbackMap.items():
            if v["callback"]==callback:
                myackid=k
                v["count"]+=1
                break
        myackid= myackid or self.ackId
        self.callbackMap[myackid]={"callback":callback,"count":1}
        self.ackId+=1
        
        def callbackfun(data):
            if not data["result"]:
                self.rmcallbackById(data["ackId"])
        self.sio.emit('on',{'serverName':serverName,'eventName':eventName,'callback':myackid},callback=callbackfun)
    
    def off(self,serverName,eventName,callback):
        '''
        移除事件
        serverName: 监听事件的目标服务器名称
        eventName: 监听目标服务的事件名
        callback: 监听事件执行时的回调函数
        '''
        myackid=None
        for k,v in self.callbackMap.items():
            if v["callback"]==callback:
                myackid=k
        myackid and self.sio.emit('off',{'serverName':serverName,'eventName':eventName,'callback':myackid},callback=self.rmcallbackById)