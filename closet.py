
import appdaemon.plugins.hass.hassapi as hass

#
# Args:
#                                        
# Release Notes
# Version 1.1:                                    

class Closet(hass.Hass):

  def initialize(self):
  #  if "closet_sensor" in self.args:
    self.listen_state(self.door_open_event, self.args["closet_sensor"], new="on", duration=420)
    self.listen_state(self.door_event, self.args["closet_sensor"])
    self.set_log_level("NOTSET")


  def door_open_event(self, entity, attribute, old, new, kwargs):
    self.log("Turning off {} because door left open".format(self.args["closet_switch"]))
    self.turn_off(self.args["closet_switch"])

  def door_event(self, entity, attribute, old, new, kwargs):
    self.log("new {}".format(new))
    if new in ("Open", "on", "open", "On"):
      self.log("Turning on {}".format(self.args["closet_switch"]))
      self.turn_on(self.args["closet_switch"], brightness_pct=100)

    if new in ("Closed", "off", "closed", "Off"):
      self.log("Turning off {}".format(self.args["closet_switch"]))
      self.turn_off(self.args["closet_switch"])
