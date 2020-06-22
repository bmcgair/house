import appdaemon.plugins.hass.hassapi as hass
import datetime
import time

#
# App to manage bike presence
# Version 1.0:
#   Initial Version

class Bikes(hass.Hass):

  def initialize(self):
    
    # listen for bikes
    self.modes = self.get_app("modes")
    self.bikes = self.resolve_group("group.bikes")

    for bike in self.bikes:
      self.log("Init {} as {}".format(bike, self.get_state(bike)))
      self.listen_state(self.presence_event, bike)
      self.log("Listening to {}".format(bike))
      self.set_log_level("NOTSET")
    
  def presence_event(self, entity, attribute, old, new, kwargs):
    if old != new:
      if new == "on":
        self.log("{} has arrived.".format(entity))
        if self.modes.arrival_mode in ("Away", "OnAway", "Guest", "Cleaning", "Vacation"):
          self.log("Arrival Mode: {} and bike: {} has arrived. Opening garage door.".format(self.modes.arrival_mode, entity))
          self.turn_on("switch.garage_door_switch")
          self.turn_on("light.garage_lights")

      elif new == "off":
        self.log("{} has departed.".format(entity))

  def resolve_group(self, group, **kwargs):
    group = self.get_state(group, attribute = "all")
    return group["attributes"]["entity_id"]
