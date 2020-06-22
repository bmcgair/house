import appdaemon.plugins.hass.hassapi as hass
import requests

class decent(hass.Hass):

  def initialize(self):
    self.listen_state(self.espresso_switch, "switch.espresso_machine")
    self.set_log_level("NOTSET")

  def espresso_switch(self, entity, attribute, old, new, kwargs):

    if new == "on":
      self.espresso_power_on()

    elif new == "off":
      self.espresso_power_off()

  def espresso_power_on(self):
    power_state = float(self.get_state("sensor.espresso_machine_plug_power"))
    self.log("Plug Power: {}".format(power_state))
    if power_state < 20:
      self.log("sending ON to DE1")
      requests.get('https://trigger.macrodroid.com/d2c8fa52-b7e6-4690-abbe-2a0e06578642/on')

  def espresso_power_off(self):
    power_state = float(self.get_state("sensor.espresso_machine_plug_power"))
    self.log("Plug Power: {}".format(power_state))
    if power_state > 20:
      self.log("sending OFF to DE1")
      requests.get('https://trigger.macrodroid.com/d2c8fa52-b7e6-4690-abbe-2a0e06578642/off')
