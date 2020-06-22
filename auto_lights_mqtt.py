import appdaemon.plugins.hass.hassapi as hass
import appdaemon.plugins.mqtt.mqttapi as mqtt
                                     
#
# App to turn lights on when motion detected then off again after a delay
# Use with constraints to activate only in specific mode
# This version uses mqtt directly from appdaemon for speed
#      
# Args:
#                                        
# sensor: binary sensor to use as trigger                                                                                  
# leader :  master room light       
# followers : slave room lights
# hold : HE virtual switch to enable room light level hold for 1hr
# delay: amount of time after turning on to turn off again in normal operation
# constraint_input_select: modes this app will run in
# hi mid low: % settings for bulb levels based on outdoor lux
# zone: outdoor lux sensor zone
# night: nightlight setting %

#              
# Release Notes
#             
# Version 1.1:                                    
#   Add ability for other apps to cancel the timer
                              
class AutoLightsMqtt(mqtt.Mqtt, hass.Hass):
                       
  def initialize(self):
    self.handle = None
    self.sunlight = self.get_app("sunlight")
    self.prefix = "homie/he/"

    
    # Subscribe to sensors   
    if "sensor" in self.args:                            
      self.mqtt_subscribe(self.prefix + self.args["sensor"], namespace="mqtt")
      self.listen_event(self.motion, "MQTT_MESSAGE", topic = self.prefix + self.args["sensor"] + "/motion/status", namespace="mqtt")
    else:                                           
      self.log("No sensor specified, doing nothing")

    if "leader" in self.args:
      self.mqtt_subscribe(self.prefix + self.args["leader"], namespace="mqtt")

    if "followers" in self.args:
      self.mqtt_subscribe(self.prefix + self.args["followers"], namespace="mqtt")

    if "switches" in self.args:
      self.mqtt_subscribe(self.prefix + self.args["switches"], namespace="mqtt")

    if "room" in self.args:
      self.mqtt_subscribe(self.prefix + self.args["room"], namespace="mqtt")

    if "hold" in self.args:
      self.log("toggling hold {}".format(self.args["hold"]))
      self.turn_on(self.args["hold"], brightness_pct=0)
      self.turn_off(self.args["hold"])

  def getLevels(self, kwargs):

    if self.get_state("input_select.holman_mode") != "Night":
      if self.args["zone"] == "west":
        try:
          self.sunlight.west_level
        except:
          self.level = "high"
        else:
          self.level = str(self.sunlight.west_level)
          self.log("West Level: {}".format(self.sunlight.west_level))

      elif self.args["zone"] == "east":
        try:
          self.sunlight.east_level
        except:
          self.level = "high"
        else:
          self.level = str(self.sunlight.east_level)
          self.log("East Level: {}".format(self.sunlight.east_level))
      else:
        self.level = "high"

      if self.level == "off":
        self.level_on = 0
        self.level_off = 0

      elif self.level == "mid":
        self.level_on = self.args[self.level]
        self.level_off = 0

      elif self.level == "high":
        self.level_on = self.args[self.level]
        self.level_off = self.args["low"]

      self.log("Level off percent {}".format(self.level_off))
      self.log("Level on percent {}".format(self.level_on))
    else:
      self.cancel()
      self.turn_off(self.args["hold"])
      self.level_on = self.args["night"]
      self.level_off = 0

  def motion(self, event_name, data, kwargs):
    if "hold" in self.args:
      holdState = self.get_state(self.args["hold"])
      self.log("Hold is: {}".format(holdState))

    if data['payload'] == "active":          
      self.log("Motion active")
      self.getLevels(self)
      self.cancel()

      if holdState == "off" or holdState == None:
        if self.level_on != 0:
          if "switches" in self.args:
            self.mqtt_publish(self.prefix + self.args["switches"] +"/onoff/set", "true" , namespace="mqtt")

          if "room" in self.args:                                                                             
            self.log("Setting room {} to {}".format(self.args["room"],self.level_on))
            self.mqtt_publish(self.prefix + self.args["room"] + "/dim/set", self.level_on , namespace="mqtt")

      elif holdState == "on":
        holdLevel = round(self.get_state(self.args["hold"], attribute="brightness")/2.54)
        self.log("Hold active. Hold Level: {}".format(holdLevel))
        if "room" in self.args:                                                                             
          self.log("Setting room {} to {}".format(self.args["room"],holdLevel))
          self.mqtt_publish(self.prefix + self.args["room"] +"/dim/set", holdLevel , namespace="mqtt")
                                  
    elif data['payload'] == "inactive":
      self.log("Motion inactive")
      self.getLevels(self)
      if holdState == "off" or holdState == None:                              
        if "delay" in self.args and self.get_state("input_select.holman_mode") != "Night":    
          delay = self.args["delay"]
        else:       
          delay = 40       
      elif holdState == "on":
        delay = 3600       
      self.handle = self.run_in(self.zone_off, delay)
      self.log("Turning down in {} seconds".format(delay))
                             
  def zone_off(self, kwargs):  
    if "followers" in self.args:                   
      self.mqtt_publish(self.prefix + self.args["followers"] +"/onoff/set", "false" , namespace="mqtt")

    if "leader" in self.args:                                                                        
      self.log("Time is up. Turning down leader {} to {}".format(self.args["leader"],self.level_off))
      if self.get_state("input_select.holman_mode") != "Night":

          if self.args["low"] == 0 or int(self.get_state("sensor.multisensor_deck_illuminance")) > 100:
            self.mqtt_publish(self.prefix + self.args["leader"] +"/onoff/set", "false" , namespace="mqtt")
          else:
            self.mqtt_publish(self.prefix + self.args["leader"] +"/dim/set", self.level_off , namespace="mqtt")

      else:
          self.mqtt_publish(self.prefix + self.args["leader"] +"/onoff/set", "false" , namespace="mqtt")

    if "hold" in self.args:
      self.log("Hold is up. Turning off {}".format(self.args["hold"]))
      self.turn_off(self.args["hold"])

  def cancel(self):               
    self.cancel_timer(self.handle)
