import appdaemon.plugins.hass.hassapi as hass
import datetime
import time
import requests

# Args
# alarm_switch: hubitat dimmer set by alexa for alarm use

class WakeUp(hass.Hass):

  def initialize(self):
    self.handle_espresso = None
    self.handle_hvac = None
    self.handle_lights = None
    self.handle_wakeup = None
    self.hvac = self.get_app("hvac")

    self.parse_alarm(alarm = self.get_state(self.args["alarm_switch"], attribute= "brightness"))
    self.set_timers()

    # Set alarm on change
    self.listen_state(self.alarm_set_event, self.args["alarm_switch"], attribute= "brightness")

  def parse_alarm(self, **kwargs):
    alarm = kwargs.get('alarm', 206)
    self.log("Alarm raw: {}".format(alarm))
    if alarm in (127, 128):
      self.wakeup = datetime.time(5, 00, 0)
    elif alarm == 130:
      self.wakeup = datetime.time(5, 15, 0)
    elif alarm in (132, 133):
      self.wakeup = datetime.time(5, 30, 0)
    elif alarm == 135:
      self.wakeup = datetime.time(5, 45, 0)
    elif alarm == 153:
      self.wakeup = datetime.time(6, 00, 0)
    elif alarm in (155, 156):
      self.wakeup = datetime.time(6, 15, 0)
    elif alarm == 158:
      self.wakeup = datetime.time(6, 30, 0)
    elif alarm in (160, 161):
      self.wakeup = datetime.time(6, 45, 0)
    elif alarm == 178:
      self.wakeup = datetime.time(7, 00, 0)
    elif alarm == 181:
      self.wakeup = datetime.time(7, 15, 0)
    elif alarm in (183, 184):
      self.wakeup = datetime.time(7, 30, 0)
    elif alarm == 186:
      self.wakeup = datetime.time(7, 45, 0)
    elif alarm == 204:
      self.wakeup = datetime.time(8, 00, 0)
    elif alarm in (206, 207):
      self.wakeup = datetime.time(8, 15, 0)
    elif alarm == 209:
      self.wakeup = datetime.time(8, 30, 0)
    elif alarm in (211, 212):
      self.wakeup = datetime.time(8, 45, 0)
    elif alarm in (229, 230):
      self.wakeup = datetime.time(9, 00, 0)
    elif alarm == 232:
      self.wakeup = datetime.time(9, 15, 0)
    elif alarm in (234, 235):
      self.wakeup = datetime.time(9, 30, 0)
    elif alarm == 237:
      self.wakeup = datetime.time(9, 45, 0)
    elif alarm in (25, 26):
      self.wakeup = datetime.time(10, 00, 0)
    elif alarm == 28:
      self.wakeup = datetime.time(10, 15, 0)
    elif alarm in (30, 31):
      self.wakeup = datetime.time(10, 30, 0)
    elif alarm == 33:
      self.wakeup = datetime.time(10, 45, 0)
    else:
      self.wakeup = datetime.time(7, 00, 0)
      

  def alarm_set_event(self, entity, attrubite, old, new, kwargs):
    self.parse_alarm(alarm=new)
    self.set_timers()
    self.log("Alarm he: {}".format(new))

  def set_timers(self):
    self.cancel()
    self.espresso_on = (datetime.datetime.combine(datetime.date(1, 1, 1), self.wakeup) - datetime.timedelta(minutes=30)).time()
    self.lights_on = (datetime.datetime.combine(datetime.date(1, 1, 1), self.wakeup) - datetime.timedelta(minutes=15)).time()
    self.hvac_on = (datetime.datetime.combine(datetime.date(1, 1, 1), self.wakeup) - datetime.timedelta(minutes=self.hvac_pre())).time()
    self.handle_espresso = self.run_daily(self.run_espresso, self.espresso_on)
    self.handle_hvac = self.run_daily(self.run_hvac, self.hvac_on)
    self.handle_lights = self.run_daily(self.run_lights, self.lights_on)
    self.handle_wakeup = self.run_daily(self.run_wakeup, self.wakeup)
    self.log("Alarm Set for: {}".format(self.wakeup))
    self.log("Espresso Equipment On: {}".format(self.espresso_on))
    self.log("Light Fade Start: {}".format(self.lights_on))
    self.log("HVAC On: {}".format(self.hvac_on))

  def hvac_pre(self):
    outdoor_temp=int(float(self.get_state("sensor.arbor_lodge_temp")))
    if -50 <= outdoor_temp <= 33: 
      minutes = 20
    elif 34 <= outdoor_temp <= 42:
      minutes = 15
    elif 43 <= outdoor_temp <= 52:
      minutes = 11
    elif 53 <= outdoor_temp <= 150:
      minutes = 6
    else:
      minutes = 1
    self.log("Outdoor Temp: {}F. HVAC Pre: {}m before wakeup".format(outdoor_temp,minutes))
    return minutes

  def run_lights(self, kwargs):
      self.turn_off("light.outside_lights")
      self.turn_on("light.bedside_lights", brightness=1)
      self.turn_on("light.bedroom_light", brightness=1)
      self.brightness=1
      self.log("Starting lights. Brightness = {}".format(self.brightness))
      self.turn_on("light.bedside_lights", brightness_pct=self.brightness)
      self.turn_on("light.bedroom_light", brightness_pct=self.brightness)
      self.fade(self)

  def run_espresso(self, kwargs):
      #self.hvac.econet_auth()
      self.log("Starting Espresso")
      self.turn_on("switch.espresso_grinder")
      self.turn_on("switch.espresso_machine")
      self.de_count = 0
      self.run_in(self.spam_de1, 90)

  def spam_de1(self, kwargs):
      self.de_count = self.de_count +1
      if self.de_count < 5:
        self.log("Spam DE1 attempt: {}".format(self.de_count))
        if float(self.get_state("sensor.espresso_machine_plug_power")) < 20:
          self.log("spam ON to DE1 on attempt: {}".format(self.de_count))
          requests.get('https://trigger.macrodroid.com/d2c8fa52-b7e6-4690-abbe-2a0e06578642/on')
        self.run_in(self.spam_de1,300)

  def run_hvac(self, kwargs):
    self.turn_on("switch.hot_water_tank")
    self.log("Starting HVAC")
    self.hvac.thermostat_mode({"hmode":"auto"})
    self.call_service("climate/set_temperature", entity_id = "climate.thermostat", target_temp_high=self.args["upper"], target_temp_low=self.args["lower"])

  def run_wakeup(self, kwargs):
      self.log("Starting Wakeup")
      self.turn_on("light.bedroom_lights", brightness_pct=30)
      self.hvac.thermostat_mode({"hmode":"auto"})
      self.call_service("climate/set_temperature", entity_id = "climate.thermostat", target_temp_high=self.args["upper"], target_temp_low=self.args["lower"])
      self.turn_on("light.hallway_ceiling_light", brightness_pct=15)
      self.turn_on("light.kitchen_rear", brightness_pct=15)
      self.turn_on("light.kitchen_sink", brightness_pct=15)
      self.turn_on("switch.hot_water_loop")
      self.run_in(self.present_cb, 10)
      self.turn_off("switch.bill_s_alexa_apps_do_not_disturb_switch")

  def present_cb(self, kwargs):
   self.select_option("input_select.holman_mode", "Present")

  def fade(self, kwargs):
    # Send another one here because Decent
    self.log("Fade brightness = {}".format(self.brightness))
    self.brightness = self.brightness +1
    if self.brightness < 15:
      self.turn_on("light.bedroom_lights", brightness_pct=self.brightness)
      self.run_in(self.fade,60)

  def cancel(self):               
    self.log("Cancel existing timers")
    self.cancel_timer(self.handle_espresso)
    self.cancel_timer(self.handle_lights)
    self.cancel_timer(self.handle_hvac)
    self.cancel_timer(self.handle_wakeup)
