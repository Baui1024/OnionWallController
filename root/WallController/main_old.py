import dbus
import re


managed_objects = {} # dict: deep nested dictionary structure
devices_by_adr = {} # dict: key: device id, value: info about the device
agent = None # instance of "Agent", see below
agent_manager = None
usb_bt_mac = ""
usb_bt_power = False
usb_bt_discoverable = False
usb_bt_pairable = False
usb_bt_interface = 'org.bluez.Adapter1'
phones = {}
 
def my_pprint(obj, intend = 0):
    """Pretty-pring nested dicts & lists
    """                          
    if isinstance(obj, dict):                                       
        for key, value in obj.items():                           
            print(intend*" "+str(key)+" : ")                 
            my_pprint(value, intend = intend + 4)           
            print()                                                 
    elif isinstance(obj, list):                                      
        for value in obj:                                        
            my_pprint(value, intend = intend + 4)            
            print()                                          
    elif isinstance(obj, bytes):                                     
        print("<binary data>")                                   
                                                                        
    else:                                                            
        try:                                                     
            print(intend*" "+str(obj))                       
        except UnicodeDecodeError:                               
            print(intend*" ""<?>")                          

def get_objects():
    """Some dbus interfaces implement a "manager":
    
    https://dbus.freedesktop.org/doc/dbus-specification.html#standard-interfaces
    You can check if we have one for "org.bluez" like this:
    ::
    
        gdbus introspect --system --dest org.bluez --object-path /
    Let's get one
    """
    global managed_objects
    
    managed_objects = {}
    
    proxy_object = bus.get_object("org.bluez","/")
    manager = dbus.Interface(proxy_object, "org.freedesktop.DBus.ObjectManager")
    managed_objects = manager.GetManagedObjects()
    usb_bt_mac = managed_objects["/org/bluez/hci0"]["org.bluez.Adapter1"]['Address']
    usb_bt_power = bool(managed_objects["/org/bluez/hci0"]["org.bluez.Adapter1"]['Powered'])
    usb_bt_discoverable = bool(managed_objects["/org/bluez/hci0"]["org.bluez.Adapter1"]['Discoverable'])
    usb_bt_pairable = bool(managed_objects["/org/bluez/hci0"]["org.bluez.Adapter1"]['Pairable'])
    #print(usb_bt_mac)
    #my_pprint(managed_objects["/org/bluez/hci0"]["org.bluez.Adapter1"])
    #my_pprint(managed_objects)
    #my_pprint(managed_objects) # enable this to see the nested dictionaries nested 

def get_devices():
    """Populates the devices_by_adr dictionary
    """
    global managed_objects
    global devices_by_adr
    
    devices_by_adr = {}
    
    r = re.compile("\/org\/bluez\/hci\d*\/dev\_(.{17})$")
    #r = re.compile("\/org\/bluez\/hci\d*\/dev\_(.*)")
    # e.g., match a string like this:
    # /org/bluez/hci0/dev_58_C9_35_2F_A1_EF
    
    for key, value in managed_objects.items():
        #print("get_devices()")
        
        m = r.match(key)
        #print(m)
        #print("key=", key, m)
        if m is not None:
            dev_str = m.group(1) # we have a device string!
            # print("dev_str=", dev_str)
            # let's flatten that dict a bit
            devices_by_adr[dev_str] = value["org.bluez.Device1"]
                        

def get_proxy():
    """Adapter API:  
    https://git.kernel.org/pub/scm/bluetooth/bluez.git/tree/doc/adapter-api.txt
    Returns an object with all those methods, say StartDiscovery, etc.
    """
    # use [Service] and [Object path]:
    device_proxy_object = bus.get_object("org.bluez","/org/bluez/hci0")
    # use [Interface]:
    return device_proxy_object

def get_media_proxy():
    # use [Service] and [Object path]:
    device_proxy_object = bus.get_object("org.bluez","/org/bluez/hci0/dev_8C_7A_AA_55_44_26/player0")
    # use [Interface]:
    #adapter = dbus.Interface(device_proxy_object,"org.bluez.MediaPlayer1") #This is the  media interface to play/pause etc.
    return device_proxy_object


def get_audio_information():
    """
       Registers a mediaplayer to a connected client. 
    """
    try:
        dbus_iface = dbus.Interface(get_media_proxy(),"org.freedesktop.DBus.Properties") #This is the generic interface to set/get properties
       # dbus_iface.Stop( )
        probs = dbus_iface.GetAll("org.bluez.MediaPlayer1")
        my_pprint(probs)

    except dbus.DBusException:
        raise

def get_device(dev_str):
    """Device API:
    
    https://git.kernel.org/pub/scm/bluetooth/bluez.git/tree/doc/device-api.txt
    
    Returns an object with all those methods, say Connect, Disconnect, Pair, etc
    """
    #print("devstring; ",dev_str)
    # use [Service] and [Object path]:
    device_proxy_object = bus.get_object("org.bluez","/org/bluez/hci0/dev_"+dev_str)
    # use [Interface]:
    device1 = dbus.Interface(device_proxy_object,"org.bluez.Device1")
    return device1


def clear_all_devices():
    """Clears all found bt devices from  .. a cache?
    
    After this, you have to run discovery again
    """
    proxy = get_proxy()
    dbus_iface = dbus.Interface(get_proxy(),"org.bluez.Adapter1")
    for key in devices_by_adr.keys():
        device = get_device(key)
        try:
            dbus_iface.RemoveDevice(device) 
        except dbus.DBusException:
            print("could not remove", device)

def start_pairing_mode():
    """
        Sets the adapter into Discoverable Mode and Pairable Mode
    """
    try:
        dbus_iface = dbus.Interface(get_proxy(),"org.freedesktop.DBus.Properties") #This is the generic interface to set/get properties
        if not dbus_iface.Get(usb_bt_interface,"Powered"):
            dbus_iface.Set(usb_bt_interface,"Powered",dbus.Boolean(True))
        clear_all_devices() #disconnects other devices first
        dbus_iface.Set(usb_bt_interface,"Discoverable",dbus.Boolean(True))
        dbus_iface.Set(usb_bt_interface,"Pairable",dbus.Boolean(True))
    except dbus.DBusException:
        raise

def stop_play():
    
    try:

        dbus_iface = get_media_proxy(devices_by_adr[0])
        all = dbus_iface.GetAll(usb_bt_interface)
        my_pprint(all)
    except dbus.DBusException:
        raise


def main():        
    global bus 
    try:      
        bus = dbus.SystemBus()
        get_objects()
        get_devices()            
        get_proxy()
        get_audio_information()
        #stop_play()
        start_pairing_mode()
        #x = input("1 = Disconnect all Devices, 2 = pairing mode: \n")

        #if x == "1":
        #    clear_all_devices()
        #elif x == "2":
        #    start_pairing_mode()
        #    pass

        #get_devices()
        #clear_all_devices()                                      
        #bluetooth = bus.get_object("org.bluez","/org/bluez/hci0")
        #print("got client!")
                                                                    
        #adapter = dbus.Interface(bluetooth,"org.bluez.Adapter1")
        #print(adapter)    
    except dbus.DBusException:
        raise
                          
                          
                          
                          
              
 
 
                          
              
                          
if __name__ == '__main__':
    main()
