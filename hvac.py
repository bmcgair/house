import appdaemon.plugins.hass.hassapi as hass
import datetime
import time
import requests
import json


class hvac(hass.Hass):
  def initialize(self):
    self.handle = None

    if "windowsDoors" in self.args:                            
      self.log("windowsDoors {}".format(self.args["windowsDoors"]))
      self.listen_state(self.monitor, self.args["windowsDoors"])

    else:                                           
      self.log("No Windows or Doors specified, doing nothing")

  def monitor(self, entity, attribute, old, new, kwargs):
    mode = self.get_state("input_select.holman_mode")

    if (new == "off" and old == "on") and mode == "Present": 
      self.log("Windows and Doors closed and mode is {}. Resuming hvac.".format(mode))
      self.cancel()
      self.thermostat_mode({"hmode":"auto"})

    elif new == "on" and old == "off":
      self.log("Windows or Doors Open. Turning hvac off in 60 seconds.")
      self.cancel()
      self.handle = self.run_in(self.thermostat_mode, 60, hmode = "off" )

  def thermostat_mode(self, kwargs):
    mymode = kwargs.get('hmode', "off")
    openings = self.get_state("group.hvac_monitor")
    self.log("Windows and Doors: {}".format(openings))

    if openings == "off" or ( openings ==  "on" and mymode == "off" ):
      self.call_service("climate/set_hvac_mode", entity_id = "climate.thermostat", hvac_mode=mymode)

  def resolve_group(self, group, **kwargs):
    group = self.get_state(group, attribute = "all")
    return group["attributes"]["entity_id"]

  def set_contacts(self, win_list, state):
    for win in win_list:
      munge = win.split(".")
      munge_win = munge[1].replace("_", "-")
      munge_final= munge_win.rsplit("-",1)[0]
      mytopic = "homie/he/" + munge_final + "/contact/status"
      self.log("Init window topic {} {}".format(mytopic,state))
      self.call_service("mqtt/publish", topic = mytopic, payload = state)

  def cancel(self):
    self.cancel_timer(self.handle)

