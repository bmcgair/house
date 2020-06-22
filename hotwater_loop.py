import appdaemon.plugins.hass.hassapi as hass
                                     
#
# App to turn lights on when motion detected then off again after a delay
# Use with constraints to activate only in specific mode
#      
# Args:
#                                        
# motion_sensors: motion sensors in areas where we want to trigger hw loop
# temp_sensor: name of temp sensor on hw return
#             
# Version 1.1:                                    
class HotWaterLoop(hass.Hass):
                       
  def initialize(self):
    self.handle = None
    try:
      self.wh_temp = self.get_state("water_heater.water_heater", attribute="temperature")

    except:
      self.wh_temp = 120
                          
    # Subscribe to sensors   
    if "motion_sensors" in self.args:                            
      motion_sensors = self.args["motion_sensors"].split(",")
      for sensor in motion_sensors:
        self.log("Listening to Motion Sensor: {}".format(sensor))
        self.listen_state(self.motion, sensor)
    else:                                           
      self.log("No motion sensor specified, doing nothing")
    
    if "temp_sensor" in self.args:                            
      self.log("Listening to Temp Sensor: {}".format(self.args["temp_sensor"]))
      self.listen_state(self.temp, self.args["temp_sensor"])
    else:                                           
      self.log("No temp sensor specified, doing nothing")
                                                        
  def motion(self, entity, attribute, old, new, kwargs):
    temp = int(self.get_state(self.args["temp_sensor"]))  
    try:
      self.wh_temp = self.get_state("water_heater.water_heater", attribute="temperature")
    except:
      self.wh_temp = 120
    min_threshold = self.wh_temp-25
    self.log("Motion active: {}. WH SetPt: {} Current: {} Min: {}".format(entity, self.wh_temp, temp, min_threshold))
    if new == "on":          
      if temp < min_threshold:
        self.log("Current: {} below Min: {}. Turning hotwater loop on".format(temp,min_threshold))
        self.turn_on("switch.hot_water_loop")

  def temp(self, entity, attribute, old, new, kwargs):
    max_threshold = self.wh_temp-10
    self.log("WH SetPt: {} Max: {}".format(self.wh_temp,max_threshold))

    switch_state = self.get_state("switch.hot_water_loop")
    self.log("Hot Water Loop is {}. Current: {} Max: {}".format(switch_state,new, max_threshold))
    if switch_state == "on":
      if int(new) > max_threshold:
        self.log("Current: {} above Max: {}. Turning hotwater loop off".format(new,max_threshold))
        self.turn_off("switch.hot_water_loop")
