import appdaemon.plugins.hass.hassapi as hass
import time
                                     
#
# Args:
#                                        
# sensor: binary sensor to use as trigger                                                                                  
# delay: amount of time after turning on to turn off again in normal operation
# zone: zone name
# speakers: audio devices
# video_switcher: receiver device
# display: display device
# display_switch: the display switch in hubitat
# constraint_input_select: modes this app will run in
#              
# Release Notes
# Version 1.1:                                    
#   Add ability for other apps to cancel the timer
                              
class AutoAV(hass.Hass):
                       
  def initialize(self):
    self.handle = None
    self.sunlight = self.get_app("sunlight")
    self.set_log_level= "INFO"

    # Subscribe to sensors   
    if "sensor" in self.args:                            
      self.listen_state(self.motion, self.args["sensor"])
    else:                                           
      self.log("No sensor specified, doing nothing")
                                                        
    if "display_switch" in self.args:                            
      self.listen_state(self.display_switch, self.args["display_switch"])
      self.listen_state(self.roku_set_event, self.args["display_switch"], attribute="brightness")

    else:                                           
      self.log("No display_switch specified, audio only zone")

  def motion(self, entity, attribute, old, new, kwargs):
    if new == "on":          
      self.log("Motion active")
      self.cancel()
      self.motion_on()

    elif (new == "off" and old == "on"):
      self.log("Motion inactive")
      if "delay" in self.args:    
        delay = self.args["delay"]
      else:       
        delay = 3600    
      self.handle = self.run_in(self.motion_off, delay)
      self.log("Turning off speakers in {} seconds".format(delay))
                            
  def display_switch(self, entity, attribute, old, new, kwargs):
    if new == "on" and self.get_state(self.args["display"]) != "on":
      self.log("TV switch on zone: {}".format(self.args["zone"]))
      self.cancel()
      self.zone_on()

    elif new == "off" and self.get_state(self.args["display"]) != "off":
      self.run_in(self.zone_off, 0)

  def zone_on(self):
    if "display_switch" in self.args and self.get_state(self.args["video_switcher"]) == "off":
      self.log("Turn on everything")
      self.speakers_on(self.args["speakers"])
      for x in range(5):
        self.run_in(self.force_tv, 1, desired_state = "on")
        time.sleep(0.5)
      self.run_in(self.select_sources, 12)
    else:
      self.call_service("media_player/turn_on", entity_id = self.args["display"])
      self.run_in(self.select_sources, 0)

      try:
        self.sunlight.east_level
      except:
        east_level = "high"
      else:
        east_level = str(self.sunlight.east_level)
        self.log("East Level: {}".format(self.sunlight.east_level))

      if east_level == "high":
        self.level_on= 20
        self.log("TV lights on")
      else:
        self.level_on= 0
        self.log("No TV lights needed")

      self.turn_on("light.living_room_hold", brightness_pct= self.level_on)
      self.turn_on("light.living_room_lights", brightness_pct= self.level_on)
      self.log("av turning on lights to hold {} ".format(self.level_on))

    if self.get_state(self.args["display"]) != self.get_state(self.args["display_switch"]):
      self.log("Display in zone {} status: {}. Should be: {}. Attempting to force on".format(self.args["zone"], self.get_state(self.args["display"]), self.get_state(self.args["display_switch"]) ))
      for x in range(5):
        self.run_in(self.force_tv, 1, desired_state = "on")
        time.sleep(0.5)

  def motion_on(self):
    if "display_switch" not in self.args or self.get_state(self.args["display_switch"]) == "off":
      self.speakers_on(self.args["speakers"])
      self.log("Turn on speakers.")
    if "video_switcher" in self.args and self.get_state(self.args["display_switch"]) != "on":
      self.speakers_on(self.args["speakers"])
      self.run_in(self.select_sources, 12)

  def motion_off(self, kwargs):  
    if "display_switch" not in self.args: 
      self.speakers_off(self.args["speakers"])

    if "display_switch" in self.args and self.get_state(self.args["display_switch"]) == "off":
      self.run_in(self.select_sources, 0)
      self.speakers_off(self.args["speakers"])

  def zone_off(self, kwargs):  
    if "display_switch" in self.args and self.get_state(self.args["display_switch"]) == "off":
      for x in range(5):
        self.run_in(self.force_tv, 1, desired_state = "off")
        time.sleep(0.5)
      self.run_in(self.select_sources, 0)
      self.turn_off("light.living_room_hold")
    if self.get_state(self.args["display"]) != self.get_state(self.args["display_switch"]):
      self.log("Display in zone {} status: {}. Should be: {}. Attempting to force off.".format(self.args["zone"], self.get_state(self.args["display"]), self.get_state(self.args["display_switch"]) ))
      for x in range(5):
        self.run_in(self.force_tv, 1, desired_state = "off")
        time.sleep(0.5)
    
  def force_tv(self, kwargs):
    desired_state=kwargs["desired_state"]
    self.log("force tv {}".format(desired_state))
    if desired_state == "off":
      self.call_service("media_player/turn_off", entity_id = self.args["display"])
    elif desired_state == "on":
      self.call_service("media_player/turn_on", entity_id = self.args["display"])
    
  def speakers_off(self, speakers):
    speaker_list = speakers.split(",")
    for speaker in speaker_list:                                         
      self.log("Time is up. Turning speaker {} off".format(speaker))
      self.turn_off(speaker)

  def speakers_on(self, speakers):
    speaker_list = speakers.split(",")
    for speaker in speaker_list:
      self.log("Turning speaker {} on".format(speaker))
      self.turn_on(speaker)

  def roku_set_event(self, entity, attribute, old, new, kwargs):
    if new != None:
      self.parse_roku(roku=new)

  def parse_roku(self, **kwargs):
    zone = self.args["zone"]
    roku = round(int(kwargs["roku"])/2.54)
    if zone == "livingroom": 
      if roku in range(9,11):
        self.log("Roku {}: Plex.".format(zone))
        self.call_service("media_player/select_source", entity_id ="media_player.roku_yp008t412318", source="13535")
      if roku in range(19,21):
        self.log("Roku {}: Live TV.".format(zone))
        self.call_service("media_player/select_source", entity_id="media_player.roku_yp008t412318", source="195316")
      if roku in range(29,31):
        self.log("Roku {}: Prime Video.".format(zone))
        self.call_service("media_player/select_source", entity_id="media_player.roku_yp008t412318", source="13")
      if roku in range(39,41):
        self.log("Roku {}: YouTube.".format(zone))
        self.call_service("media_player/select_source", entity_id="media_player.roku_yp008t412318", source="837")
      if roku in range(49,51):
        self.log("Roku {}: Amazon Music.".format(zone))
        self.call_service("media_player/select_source", entity_id="media_player.roku_yp008t412318", source="14362")

  def select_sources(self, kwargs):                             
    self.log("Setting hardware sources")
    zone = self.args["zone"]
    display_status = self.get_state(self.args["display_switch"])
    self.log("select_sources: zone {} display switch status: {}".format(zone, display_status))
    if zone == "livingroom" and display_status == "on":
      self.log("Switch to Roku, movie")
      self.call_service("remote/turn_on", entity_id = "remote.artison")
      self.call_service("remote/send_command", entity_id = "remote.artison", command = "movie")
      self.call_service("media_player/turn_on", entity_id = self.args["video_switcher"])
      self.call_service("media_player/select_source", entity_id = self.args["display"], source = "810ES")
      self.call_service("media_player/select_source", entity_id = self.args["video_switcher"], source = "Roku")
    elif zone == "livingroom" and display_status == "off":
      self.log("Switch to Alexa, music")
      self.call_service("remote/turn_on", entity_id = "remote.artison")
      self.call_service("remote/send_command", entity_id = "remote.artison", command = "music")
      self.call_service("media_player/turn_on", entity_id = self.args["video_switcher"])
      self.call_service("media_player/select_source", entity_id = self.args["video_switcher"], source = "Alexa")
    else:  
      self.log("No Display in this zone")

  def cancel(self):               
    self.cancel_timer(self.handle)
