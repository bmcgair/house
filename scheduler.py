import appdaemon.plugins.hass.hassapi as hass
import datetime
from dateutil.parser import parse

# Declare Class
class atDaily(hass.Hass):
  def initialize(self):
    self.runtime = parse(self.args["time"]).time()

    if self.args["state"] == "off":
      self.run_daily(self.daily_off, self.runtime)

    elif self.args["state"] == "on":
      self.run_daily(self.daily_on, self.runtime)

    elif self.args["state"] == "alarm":
      self.run_daily(self.set_alarm, self.runtime)

    self.log("Scheduling {} {} Daily at {}".format(self.args["myentities"],self.args["state"],self.runtime)) 

  def set_alarm(self, kwargs):
    self.alarm = self.get_app("wakeup")
    self.alarm.set_timers()
    self.log("alarm set")

  def daily_on(self, kwargs):
    self.turn_on(self.args["myentities"])
    self.log("Turned on {} at {}".format(self.args["myentities"],self.runtime))

  def daily_off(self, kwargs):
    if "myentities" in self.args:                   
        myentities = self.args["myentities"].split(",")
        for myentity in myentities:                                         
          self.turn_off(myentity)
          self.log("Turned off {} at {}".format(myentity,self.runtime))
