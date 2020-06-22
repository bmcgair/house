import appdaemon.plugins.hass.hassapi as hass
from notify import notify
#                                        
# Version 1.1:                                    
class GarageDoor(hass.Hass):

  def initialize(self):
    self.handle = None
    self.listen_state(self.garage_door_switch, "switch.garage_door_switch")
    self.listen_state(self.garage_door_sensor, "binary_sensor.garage_door_sensor_contact")
    self.set_log_level("DEBUG")

  def garage_door_switch(self, entity, attribute, old, new, kwargs):
    door_state = self.get_state("binary_sensor.garage_door_sensor_contact")
    mode = self.get_state("input_select.holman_mode")
    self.log("Switch is: {} Sensor is: {}:".format(new, door_state))

    if door_state != new: 
      if mode == "Present":
        self.log("Pushing button")
        self.turn_on("switch.garage_door_button")

      elif mode != "Present" and door_state in ( "on", "On", "Open", "open"):
        self.log("Pushing button")
        self.turn_on("switch.garage_door_button")

      else:
        self.log("Refusing to push button when door state is {} and mode is {}.".format(door_state, mode))

      self.run_in(self.check_state, 22)

  def garage_door_sensor(self, entity, attribute, old, new, kwargs):
    switch_state_raw = self.get_state("switch.garage_door_switch")
    mode = self.get_state("input_select.holman_mode")

    if new == "off":
      sensor_state = "closed"
    elif new == "on":
      sensor_state = "open"

    if switch_state_raw == "off":
      switch_state = "closed"
    elif switch_state_raw == "on":
      switch_state = "open"

    logtxt="Garage Door Sensor is: {}. Switch state is: {}.".format(sensor_state,switch_state_raw)
    self.log(logtxt)
    messagetxt="Garage Door Sensor is {}.".format(sensor_state)
    self.call_service("notify/alexa_media", target = ["media_player.kitchen", "media_player.bedroom"], message = messagetxt, data = {"type":"tts"})

    if mode != "Present" and new == "on":
      titletxt="Garage Door {} Mode: {} ".format,(new, mode)
      #notify.push_crit(self, title=titletxt, message=messagetxt)

    if mode != "Present" and new == "on":
      msg="Garage Door {} Mode: {} ".format,(new, mode)

    if switch_state != new: 
      if new == "on":
        self.log("Turning garage door switch on to match.")
        self.turn_on("switch.garage_door_switch")

      if new == "off":
        self.log("Turning garage door switch off to match.")
        self.turn_off("switch.garage_door_switch")

  def check_state (self, kwargs):
    switch_state = self.get_state("switch.garage_door_switch")
    door_state = self.get_state("binary_sensor.garage_door_sensor_contact")
    if switch_state != door_state and ( door_state is not None or new is not None ):
      self.log("Switch is: {} Sensor is: {}. Button press failed.".format(switch_state, door_state))
      if switch_state == "on":
        self.log("Retry button press")
        self.turn_on("switch.garage_door_button")

      if switch_state == "off":
        self.log("Revert garage door switch to on.")
        self.turn_on("switch.garage_door_switch")

