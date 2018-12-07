
import PyQt5
from PyQt5 import QtCore
from PyQt5 import QtBluetooth


'''
class Deviceinfo(QtCore.QObject):
    devicechanged = PyQt5.QtCore.pyqtSignal()
    def __init__(self):
        super().__init__()
        self.m_device = QtBluetooth.QBluetoothDeviceInfo()
        self.devicechanged.connect(self.emitDeviceChanged)
    def getName(self):
        return self.m_device.name()
    def getAddress(self):
        return self.m_device.address().toString()
    def emitDeviceChanged(self):
        pass
    def setDevice(self, device):
        self.m_device = device
        self.devicechanged.emit()
'''


class BleInterface(QtCore.QObject):
    #signals
    statusInfoChanged = QtCore.pyqtSignal(str , bool)
    dataReceived = QtCore.pyqtSignal(QtCore.QByteArray)
    connectedChanged = QtCore.pyqtSignal(bool)
    servicesChanged=QtCore.pyqtSignal(list)
    currentServiceChanged = QtCore.pyqtSignal(int)
    currentDeviceChanged=QtCore.pyqtSignal(int)
    def __init__(self):
        super().__init__()
        self.m_deviceDiscoveryAgent = QtBluetooth.QBluetoothDeviceDiscoveryAgent()
        self.m_notificationDesc = QtBluetooth.QLowEnergyDescriptor()
        self.m_control = None
        #self.m_servicesUuid = QtBluetooth.QBluetoothUuid()
        self.m_servicesUuid = []    #用于存放设备的服务的UUID
        self.m_service = QtBluetooth.QLowEnergyService    #用于存放设备具体使用的服务
        self.m_readCharacteristic = QtBluetooth.QLowEnergyCharacteristic()  #用于存放读取的服务的特性内容
        self.m_writeCharacteristic = QtBluetooth.QLowEnergyCharacteristic() #用于存放写入的服务的特性内容
        self.m_devices =[] #用于存放获取的设备列表
        self.m_writemode = QtBluetooth.QLowEnergyService.WriteMode()
        self.m_readTimer = QtCore.QTimer()

        self.m_connected=bool
        self.m_devicesNames = []
        self.m_services = []
        self.m_currentDevice = None
        self.m_currentService = None



        #初始化相关变量
        self.m_connected(False)
        #self.m_control(None)
        self.m_readTimer=None
        #self.m_currentService(None)
        #self.m_currentDevice(None)

        #绑定设备发现相关信号函数
        self.m_deviceDiscoveryAgent.setLowEnergyDiscoveryTimeout(500)
        self.m_deviceDiscoveryAgent.deviceDiscovered.connect(self.addDevice)
        self.m_deviceDiscoveryAgent.error.connect(self.onDeviceScanError)
        self.m_deviceDiscoveryAgent.finished.connect(self.onScanFinished)
        self.m_deviceDiscoveryAgent.canceled.connect(self.onScanFinished)
        self.dataReceived.connect(self.printDataReceived)

    def printDataReceived(self,data=QtCore.QByteArray):
        print("received data:{data}".format(data =data))

    def update_connected(self,connected=bool):
        if connected != self.m_connected:
            self.m_connected = connected
            self.connectedChanged.emit(connected)
    def set_CurrentDevice(self,indx=int):
        self.m_currentDevice=indx
        self.currentDeviceChanged.emit( indx)

    def get_CurrentDevice(self):
        return  self.m_currentDevice

    def setCurrentService(self,currentService = int):
        if self.m_currentService == currentService:
            return
        self.update_currentService(currentService)
        self.m_currentService=currentService
        self.currentServiceChanged.emit(currentService)

    def scanDevices(self):
        self.m_devices.clear()
        self.m_deviceDiscoveryAgent.start(QtBluetooth.QBluetoothDeviceDiscoveryAgent.DiscoveryMethod(2))
        print("Scanning for devices...")

    def read(self):
        if(self.m_service and self.m_readCharacteristic.isValid()):
            self.m_service.readCharacteristic(self.m_readCharacteristic)
        
    def write(self,data=bytearray()):
        print("BLEInterface write :{datawrite}".format(datawrite=data))
        if(self.m_service and self.m_writeCharacteristic.isValid()):
            if(len(data) > 20):
                sentBytes = 0
                while sentBytes < len(data):
                    self.m_service.writeCharacteristic(self.m_writeCharacteristic,data[sentBytes:sentBytes + 20],self.m_writemode)
                    sentBytes+=20
                    if self.m_writemode == QtBluetooth.QLowEnergyService.WriteWithResponse:
                        pass
                        if self.m_service.error() != QtBluetooth.QLowEnergyService.NoError:
                            return
            else:
                self.m_service.writeCharacteristic(self.m_writeCharacteristic,data,self.m_writemode)
    
    def addDevice(self, device):
        if device.coreConfigurations() & QtBluetooth.QBluetoothDeviceInfo.LowEnergyCoreConfiguration:
            self.m_devices.append(QtBluetooth.QBluetoothDeviceInfo(device))
            print("Discovered LE Device name: {name} ,Address: {address} ".format(name=device.name(),address=device.address().toString()))
            print("Low Energy device found. Scanning more...")


    def onScanFinished(self):
        if len(self.m_devices) == 0:
            print("Can't find any BLE device")
        print("Scan finished!")
        self.set_CurrentDevice(0)
        self.connectCurrentDevice()
    
    def onDeviceScanError(self,error):
        if error == QtBluetooth.QBluetoothDeviceDiscoveryAgent.PoweredOffError:
            print("The Bluetooth adaptor is powered off power it on before discovery")
        elif error == QtBluetooth.QBluetoothDeviceDiscoveryAgent.InputOutputError:
            print("Writing or reading from the device resulted in an error")
        else:
            print("An unknown error has occurred")

    def connectCurrentDevice(self):
        if len(self.m_devices) == 0:
            return
        if self.m_control:
            self.m_control.disconnectFromDevice()
            self.m_control = None
        self.m_control = QtBluetooth.QLowEnergyController(self.m_devices[self.m_currentDevice])
        self.m_control.serviceDiscovered.connect(self.onServiceDiscovered)
        self.m_control.discoveryFinished.connect(self.onServiceScanDone)
        self.m_control.error.connect(self.onControllerError)
        self.m_control.connected.connect(self.onDeviceConnected)
        self.m_control.disconnected.connect(self.onDeviceDisconnected)
        self.m_control.connectToDevice()
    
    def onDeviceConnected(self):
        self.m_servicesUuid.clear()
        self.m_services.clear()
        self.m_currentService = None
        self.servicesChanged.emit(self.m_services)
        self.m_control.discoverServices()

    def onDeviceDisconnected(self):
        self.update_connected(False)
        self.statusInfoChanged.emit("Device disconnected",False)
        print("Remote device disconnected")
       
    def onServiceDiscovered(self,gatt=QtBluetooth.QBluetoothUuid()):
         self.statusInfoChanged.emit("Service discovered. Waiting for service scan to be done...", True)
         print("Service discovered. Waiting for service scan to be done... GATT: {gatt} ".format(gatt=gatt))

    def onServiceScanDone(self):
        self.m_servicesUuid = self.m_control.services()
        if len(self.m_servicesUuid)==0:
            self.statusInfoChanged.emit("Can't find any services.", True)
            print("Can't find any services.")
        else:
            self.m_services.clear()
            for uuid in self.m_servicesUuid:
                self.m_services.append(uuid.toString())
            self.servicesChanged.emit(self.m_services)
            self.m_currentService = -1 #to force call update_currentService(once)
            self.setCurrentService(0)
            self.statusInfoChanged.emit("All services discovered.", True)
            print("All services discovered.")
            self.setCurrentService(3)

    def disconnectDevice(self):
        self.m_readTimer.deleteLater()
        self.m_readTimer=None
        if self.m_devices.isEmpty():
            return
        if self.m_notificationDesc.isValid()and self.m_serivce:
            self.m_service.writeDescriptor(self.m_notificationDesc,bytearray(0,0,0,0))
        else:
            self.m_control.disconnectFromDevice()
            self.m_service = None

    def onControllerError(self,error=QtBluetooth.QLowEnergyController.error):
        self.statusInfoChanged.emit("Cannot connect to remote device.", False)
        print("Controller Error")

    def onCharacteristicChanged(self,chara=QtBluetooth.QLowEnergyCharacteristic,value=QtCore.QByteArray):
        print("Characteristic Changed {values}".format(values=value))
        self.dataReceived.emit(value)

    def onCharacteristicWrite(self,c=QtBluetooth.QLowEnergyCharacteristic,value=QtCore.QByteArray):
        print("characteristic Written: {values}".format(values=value))


    def onCharacteristicRead(self,c=QtBluetooth.QLowEnergyCharacteristic,value=QtCore.QByteArray):
        print("Characteristic Read:  {values}".format(values=value))
        self.dataReceived.emit(value)

    def update_currentService(self,indx=int):
        self.m_service = None
        if indx>=0 and len(self.m_servicesUuid)>indx:
           self.m_service = self.m_control.createServiceObject(self.m_servicesUuid[indx])
        if not self.m_service:
            self.statusInfoChanged.emit("Service not found.", False)
            print("Service not found.")
            return
        self.m_service.stateChanged.connect(self.onServiceStateChanged)
        self.m_service.characteristicChanged.connect(self.onCharacteristicChanged)
        self.m_service.characteristicRead.connect(self.onCharacteristicRead)
        self.m_service.characteristicWritten.connect(self.onCharacteristicWrite)
        self.m_service.error.connect(self.serviceError)
        if self.m_service.state() == QtBluetooth.QLowEnergyService.DiscoveryRequired:
            self.statusInfoChanged.emit("Connecting to service...",True)
            print("Connecting to service... gatt:{gatt}".format(gatt=self.m_service.serviceUuid()))
            self.m_service.discoverDetails()
        else:
            searchCharacteristic()

    def searchCharacteristic(self):
        if self.m_service:
            for c in self.m_service.characteristics():
                if c.isValid():
                    if c.properties() & QtBluetooth.QLowEnergyCharacteristic.WriteNoResponse or c.properties() & QtBluetooth.QLowEnergyCharacteristic.Write:
                        self.m_writeCharacteristic = c
                        self.update_connected(True)
                        if c.properties() & QtBluetooth.QLowEnergyCharacteristic.WriteNoResponse:
                            self.m_writemode=QtBluetooth.QLowEnergyService.WriteWithoutResponse
                        else:
                           self.m_writemode=QtBluetooth.QLowEnergyService.WriteWithResponse
                    if c.properties() & QtBluetooth.QLowEnergyCharacteristic.Read:
                        self.m_readCharacteristic=c
                        if not self.m_readTimer:
                            self.m_readTimer=QtCore.QTimer()
                            self.m_readTimer.timeout.connect(self.read)     #此处在计时器超时时调用读取函数读取characteristic
                            self.m_readTimer.start(3000)                               #此处设定定时器读取间隔，单位ms
                    self.m_notificationDesc = c.descriptor(QtBluetooth.QBluetoothUuid(0x2902))
                    #print(QtBluetooth.QBluetoothUuid(0x2902).toString())
                    print( self.m_notificationDesc.isValid())
                    if self.m_notificationDesc.isValid():
                        #print(bytearray([1,0]))
                        self.m_service.writeDescriptor(self.m_notificationDesc,bytearray([1,0]))



    def onServiceStateChanged(self,s=QtBluetooth.QLowEnergyService.ServiceState):
        print('service state changed , state: {state}'.format(state=s) )
        if s == QtBluetooth.QLowEnergyService.ServiceDiscovered:
            self.searchCharacteristic()

    def serviceError(self,e=QtBluetooth.QLowEnergyService.ServiceError):
        print("Service error: {error}".format(error = e))

'''
class DeviceFinder(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self.m_devices = []

        self.deviceDiscoveryAgent = QtBluetooth.QBluetoothDeviceDiscoveryAgent(self)
        self.deviceDiscoveryAgent.setLowEnergyDiscoveryTimeout(500)
        self.deviceDiscoveryAgent.deviceDiscovered.connect(self.add_device)
        self.deviceDiscoveryAgent.error.connect(self.scan_error)
        self.deviceDiscoveryAgent.finished.connect(self.scan_finished)
        self.deviceDiscoveryAgent.canceled.connect(self.scan_finished)

        self.deviceDiscoveryAgent.start(QtBluetooth.QBluetoothDeviceDiscoveryAgent.DiscoveryMethod(2))

    def add_device(self, device):
        # If device is LowEnergy-device, add it to the list
        if device.coreConfigurations() and QtBluetooth.QBluetoothDeviceInfo.LowEnergyCoreConfiguration:
            self.m_devices.append(QtBluetooth.QBluetoothDeviceInfo(device))
            print("Low Energy device found. Scanning more...")

    def scan_finished(self):
        print("scan finished")
        for i in self.m_devices:
            # QtBluetooth.QBluetoothDeviceInfo.
            print('UUID: {UUID}, Name: {name}, rssi: {rssi}'.format(UUID=i.deviceUuid().toString(),
                                                                    name=i.name(),
                                                                    rssi=i.rssi()))

        # self.quit()

    def scan_error(self):
        print("scan error")

    def connectToService(self, address):
        self.deviceDiscoveryAgent.stop()

    def quit(self):
        print("Bye!")
        QtCore.QCoreApplication.instance().quit()
'''

if __name__ == "__main__":
    import sys

    app = QtCore.QCoreApplication(sys.argv)
    m_bleInterface = BleInterface()
    m_bleInterface.scanDevices()
    sys.exit(app.exec_())
   
