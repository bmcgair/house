
import appdaemon.plugins.hass.hassapi as hass

#
# Args:
#                                        
# Release Notes
# Version 1.1:                                    

class LockUp(hass.Hass):

  def initialize(self):
    self.set_log_level("DEBUG")

    if "door_sensor" in self.args:
      self.listen_state(self.door_event, self.args["door_sensor"], new="off", duration=120)

  def door_event(self, entity, attribute, old, new, kwargs):
    self.log("Locking {}".format(self.args["door_lock"]))
    self.call_service("lock/lock", entity_id=self.args["door_lock"])
