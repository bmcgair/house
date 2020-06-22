import appdaemon.plugins.hass.hassapi as hass
import datetime
import time
from notify import notify
#
# App to manage house modes
#
# This app keeps hubitat and HA modes in sync. 
#
# Args:
# alexa_mode_switch: the hubitat dimmer used by alexa to set the mode
# Since this code is very specific to my setup I haven't bothered with parameters.
#
# Release Notes
#
# Version 1.0:
#   Initial Version
#

class Modes(hass.Hass):

  def initialize(self):
    
    self.set_log_level("NOTSET")
    self.turn_on(self.args["alexa_mode_switch"])
    self.livingroom_av = self.get_app("livingroom_av")
    self.hvac = self.get_app("hvac")
    self.kitchen_av = self.get_app("kitchen_av")
    self.arrival_mode = self.get_state("input_select.holman_mode")

    # listen for mode events
    self.listen_state(self.mode_event, "input_select.holman_mode")

    # listen for alexa mode events
    self.listen_state(self.alexa_mode_event, self.args["alexa_mode_switch"], attribute="brightness")

    # listen for people
    self.people = self.resolve_group("group.people")
    for person in self.people:
      self.log("Init {} as {}".format(self.friendly_name(person), self.get_state(person)))
      self.listen_state(self.presence_event, person)
      self.log("Listening to {}".format(self.friendly_name(person)))
    
  def mode_event(self, entity, attribute, old, new, kwargs):
    self.log("Received mode change: {}".format(new))
    if old != new:
      if new == "OnAway":
        self.onaway()
        notify.pushover(self, title="Mode Change: {}".format(new), message=new)
      if new == "Cleaning":
        self.cleaning()
      if new == "Present":
        self.present()
        if self.arrival_mode in ("Away", "OnAway", "Vacation"):
          notify.pushover(self, title="Mode Change: {}".format(new), message=new)
      if new == "Night":
        self.night()
      if new == "Away":
        self.away()
        notify.pushover(self, title="Mode Change: {}".format(new), message=new)
      if new == "Vacation":
        self.vacation()
      if new == "Dori":
        self.dori()
      if new == "Guest":
        self.guest()

  # We still need this, plus alexa-mode switch in hubitat for alexa
  def alexa_mode_event(self, entity, attrubite, old, new, kwargs):
    if new == None:
      new=1
    if old == None:
      old=1
    adjusted = round(new/2.54)

    if old != new:
      if adjusted in range(9,11):
        self.select_option("input_select.holman_mode", "OnAway")

      if adjusted in range(19,21):
        self.select_option("input_select.holman_mode", "Cleaning")

      if adjusted in range(29,31):
        self.select_option("input_select.holman_mode", "Present")

      elif adjusted in range(39,41) or new == 255:
        self.select_option("input_select.holman_mode", "Night")

      elif adjusted in range(49,51):
        self.select_option("input_select.holman_mode", "Away")

      elif adjusted in range(59,61):
        self.select_option("input_select.holman_mode", "Vacation")

      elif adjusted in range(79,81):
        self.select_option("input_select.holman_mode", "Dori")

      elif adjusted in range(89,91):
        self.select_option("input_select.holman_mode", "Guest")

  def presence_event(self, entity, attribute, old, new, kwargs):
    presence_status_txt = " "
    pres = " "
    self.arrival_mode = self.get_state("input_select.holman_mode")
    if old != new:
      if new == "home":
        self.log("{} has arrived.".format(entity))
        presence_status_txt = " is home"
        pres="arrival"

      elif new == "not_home":
        self.log("{} has departed.".format(entity))
        pesence_status_txt = " has left"
        pres="departure"

      self.count_home(self.people, **kwargs)
      self.log("There are {} people home.".format(self.count))
      self.log("Mode on Arrival {}".format(self.arrival_mode))

      titletxt="{}".format(self.friendly_name(entity)) + presence_status_txt
      messagetxt="There are {} people home. Mode on {}: {}".format(self.count, pres, self.arrival_mode)
      notify.pushover(self, title=titletxt, message=messagetxt)

      if self.count >= 1:
        self.log("Unlock Doors")
        if self.arrival_mode not in ("Night"):
          self.call_service("lock/unlock", entity_id ="lock.lock_fd")
          self.call_service("lock/unlock", entity_id ="lock.lock_dtg")

        self.select_option("input_select.holman_mode", "Present")

      elif self.count < 1 and self.arrival_mode not in ("Dori","Guest","Cleaning"):
        self.call_service("lock/lock", entity_id ="lock.lock_fd")
        self.call_service("lock/lock", entity_id ="lock.lock_dtg")
        self.select_option("input_select.holman_mode", "Away")

      elif self.count < 1 and self.arrival_mode in ("Dori","Guest","Cleaning"):
        self.call_service("lock/lock", entity_id ="lock.lock_fd")
        self.call_service("lock/lock", entity_id ="lock.lock_dtg")
        self.select_option("input_select.holman_mode", "OnAway")

  def count_home(self, residents, **kwargs):
    people_home = []
    for human in residents:
      if not human in people_home:
        if self.get_state(human) == "home":
          people_home.append(human)
          self.log("{} is home".format(human))
    self.count=len(people_home)

  def resolve_group(self, group, **kwargs):
    group = self.get_state(group, attribute = "all")
    return group["attributes"]["entity_id"]          

  # Main mode functions 
  
  def present(self):
    self.turn_on("light.alexa_mode", brightness_pct=30)
    self.turn_off("light.holds")
    self.log("Running Present mode tasks")

    if float(self.get_state("sensor.arbor_lodge_solar_rad_lx")) < 3500:
      self.turn_on("light.living_room_ceiling", brightness_pct=15)
      self.turn_on("light.kitchen_sink", brightness_pct=15)
      self.turn_on("light.hallway_ceiling_light", brightness_pct=15)
      self.turn_on("light.dining_room_light", brightness_pct=15)
      self.turn_on("light.kitchen_rear", brightness_pct=15)

    if self.now_is_between("sunset - 00:45:00", "sunrise - 03:00:00"): 
      self.turn_on("light.porch_light", brightness_pct=20)
      self.turn_on("light.deck_light", brightness_pct=12)
      self.turn_on("switch.deck_steps")

    self.call_service("alarm_control_panel/alarm_disarm", entity_id ="alarm_control_panel.blink_home")
    self.call_service("alarm_control_panel/alarm_disarm", entity_id ="alarm_control_panel.alexa_guard_aab11")
    self.hvac.thermostat_mode({"hmode":"auto"})
    self.call_service("climate/set_temperature", entity_id = "climate.thermostat", target_temp_high=self.args["upper"], target_temp_low=self.args["lower"])

    self.livingroom_av.motion_on()
    self.turn_on("switch.hot_water_tank")
    #self.run_in(self.future_lock, 600, locks=["lock.lock_fd","lock.lock_dtg"], state="lock")
    
  def night(self):
    self.turn_on("light.alexa_mode", brightness_pct=40)
    self.turn_off("light.livingroom_tv")
    self.log("Running Night mode tasks")
    self.turn_off("light.holds")
    self.call_service("lock/lock", entity_id ="lock.lock_fd")
    self.call_service("lock/lock", entity_id ="lock.lock_dtg")
    self.hvac.thermostat_mode({"hmode":"auto"})

    if float(self.get_state("sensor.arbor_lodge_temp")) >= 75.0:
      self.call_service("climate/set_temperature", entity_id = "climate.thermostat", target_temp_high=self.args["upper"], target_temp_low=58)

    else:
      self.call_service("climate/set_temperature", entity_id = "climate.thermostat", target_temp_high=80, target_temp_low=58)

    self.turn_off("switch.hot_water_tank")
    self.turn_off("switch.hot_water_loop")
    self.turn_off("switch.garage_door_switch")
    self.turn_on("light.night_lights", brightness_pct=1)
    self.turn_on("group.night", brightness_pct=1)
    self.turn_off("light.livingroom_tv")
    self.force_tv("media_player.livingroom_tv")
    self.run_in(self.kitchen_av.motion_off, 0)
    self.run_in(self.livingroom_av.motion_off, 7)
    self.common_off()
    self.turn_on("switch.bill_s_alexa_apps_do_not_disturb_switch")
    self.run_in(self.future_off, 120, myentities=["light.everything"])
    self.run_in(self.announce_door_status, 15)
    self.run_in(self.future_lock, 25, locks=["lock.lock_fd","lock.lock_dtg"], state="lock")

  def onaway(self):
    self.turn_on("light.alexa_mode", brightness_pct=10)
    self.log("Running OnAway mode tasks")
    self.call_service("lock/lock", entity_id ="lock.lock_fd")
    self.call_service("lock/lock", entity_id ="lock.lock_dtg")
    
    self.turn_off("switch.garage_door_switch")
    self.turn_off("light.attic_lights")
    self.turn_off("light.garage_lights")
    self.turn_off("light.basement_lights")
    self.turn_off("light.outside_lights")
    self.turn_off("switch.hot_water_loop")
    self.turn_off("light.shop_garage_not_lights")
    self.turn_off("switch.espresso_grinder")
    self.turn_off("switch.espresso_machine")
    self.turn_off("switch.outdoor_speakers")
    self.force_tv("media_player.livingroom_tv")
    self.hvac.thermostat_mode({"hmode":"auto"})
    self.call_service("climate/set_temperature", entity_id = "climate.thermostat", target_temp_high=80, target_temp_low=62)
    self.run_in(self.future_lock, 45, locks=["lock.lock_fd","lock.lock_dtg"], state="lock")

    if self.now_is_between("sunset - 00:45:00", "sunrise - 03:00:00"): 
      self.turn_off("light.livingroom_tv")
      self.force_tv("media_player.livingroom_tv")
      self.turn_on("light.porch_light", brightness_pct=20)
      self.turn_on("light.deck_light", brightness_pct=12)
      self.turn_on("switch.deck_steps")

  def away(self):
    self.turn_on("light.alexa_mode", brightness_pct=50)
    self.turn_off("light.holds")
    self.log("Running Away mode tasks")
    self.call_service("lock/lock", entity_id ="lock.lock_fd")
    self.call_service("lock/lock", entity_id ="lock.lock_dtg")
    self.turn_off("switch.garage_door_switch")
    self.turn_off("switch.hot_water_loop")
    self.turn_off("light.garage_lights")
    self.turn_off("switch.espresso_grinder")
    self.turn_off("switch.espresso_machine")
    self.run_in (self.kitchen_av.motion_off, 0)
    self.turn_off("light.livingroom_tv")
    self.force_tv("media_player.livingroom_tv")
    self.run_in(self.livingroom_av.motion_off, 7)
    self.common_off()
    self.call_service("alarm_control_panel/alarm_arm_away", entity_id ="alarm_control_panel.blink_home")
    self.call_service("alarm_control_panel/alarm_arm_away", entity_id ="alarm_control_panel.alexa_guard_aab11")
    self.hvac.thermostat_mode({"hmode":"auto"})
    self.call_service("climate/set_temperature", entity_id = "climate.thermostat", target_temp_high=80, target_temp_low=58)
    self.run_in(self.future_off, 120, myentities=["light.all_lights"])
    self.run_in(self.future_lock, 45, locks=["lock.lock_fd","lock.lock_dtg"], state="lock")

  def vacation(self):
    self.turn_on("light.alexa_mode", brightness_pct=60)
    self.call_service("lock/lock", entity_id ="lock.lock_fd")
    self.call_service("lock/lock", entity_id ="lock.lock_dtg")
    self.log("Running Vacation mode tasks")
    self.run_in(self.kitchen_av.motion_off, 0)
    self.turn_off("light.livingroom_tv")
    self.force_tv("media_player.livingroom_tv")
    self.run_in(self.livingroom_av.motion_off, 7)
    self.turn_off("light.everything")
    self.turn_off("light.holds")
    self.hvac.thermostat_mode({"hmode":"auto"})
    self.call_service("climate/set_temperature", entity_id = "climate.thermostat", target_temp_high=95, target_temp_low=45)

  def cleaning(self):
    self.log("Running Cleaning mode tasks")
    self.turn_on("light.alexa_mode", brightness_pct=20)
    self.turn_on("light.office_lights", brightness_pct=100)
    self.turn_on("light.bedroom_lights", brightness_pct=99)
    self.turn_on("light.living_room_lights", brightness_pct=100)
    self.turn_on("light.kitchen_lights", brightness_pct=100)
    self.turn_on("light.misc_lights", brightness_pct=99)
    self.turn_on("light.holds", brightness_pct=100)
    self.force_tv("media_player.livingroom_tv")
    self.call_service("alarm_control_panel/alarm_disarm", entity_id ="alarm_control_panel.blink_home")
    self.call_service("alarm_control_panel/alarm_disarm", entity_id ="alarm_control_panel.alexa_guard_aab11")
    self.call_service("climate/set_temperature", entity_id = "climate.thermostat", target_temp_high=73, target_temp_low=58)
    self.livingroom_av.motion_on()
    self.kitchen_av.motion_on()
    self.turn_on("light.holds")

  def dori(self):
    self.log("Running Dori mode tasks")
    self.turn_on("light.alexa_mode", brightness_pct=80)
    self.turn_off("light.holds")
    self.call_service("climate/set_temperature", entity_id = "climate.thermostat", target_temp_high=80, target_temp_low=63)
    self.turn_off("light.attic_lights")
    self.turn_off("light.basement_lights")
    self.turn_off("light.outside_lights")
    self.turn_off("light.office_lights")
    self.turn_off("light.living_room_ceiling")
    self.turn_off("light.credenza_light")
    self.turn_off("light.radio_light")
    self.turn_off("light.bedroom_light")
    self.turn_off("light.kitchen_rear")
    self.turn_off("light.kitchen_front")
    self.turn_off("light.kitchen_front_lights")
    self.turn_off("light.dining_room_light")
    self.turn_off("light.bathroom_ceiling_light")
    self.turn_off("light.shop_garage_not_lights")
    self.turn_off("switch.kitchen_speakers")
    self.turn_off("switch.living_room_subwoofer")
    self.turn_off("switch.outdoor_speakers")
    self.run_in(self.kitchen_av.motion_off, 0)
    self.turn_off("light.livingroom_tv")
    self.force_tv("media_player.livingroom_tv")
    self.run_in(self.livingroom_av.motion_off, 7)
    self.call_service("alarm_control_panel/alarm_arm_away", entity_id ="alarm_control_panel.blink_home")
    self.call_service("alarm_control_panel/alarm_arm_away", entity_id ="alarm_control_panel.alexa_guard_aab11")

    if float(self.get_state("sensor.arbor_lodge_solar_rad_lx")) < 3500:
      self.turn_on("light.radio_light", brightness_pct=15)
      self.turn_on("light.credenza_light", brightness_pct=15)
      self.turn_on("light.kitchen_mid", brightness_pct=15)
      self.turn_on("light.hallway_ceiling_light", brightness_pct=15)
      self.turn_on("light.bedside_lights", brightness_pct=15)
    if self.now_is_between("sunset - 00:45:00", "sunrise - 02:00:00"): 
      self.turn_on("light.porch_light", brightness_pct=20)

  def guest(self):
    self.log("Running Guest mode tasks")
    self.turn_on("light.alexa_mode", brightness_pct=90)
    self.turn_off("light.holds")

    if float(self.get_state("sensor.arbor_lodge_solar_rad_lx")) < 3500:
      self.turn_on("light.living_room_ceiling", brightness_pct=15)
      self.turn_on("light.kitchen_sink", brightness_pct=15)
      self.turn_on("light.hallway_ceiling_light", brightness_pct=15)
      self.turn_on("light.dining_room_light", brightness_pct=15)
      self.turn_on("light.kitchen_rear", brightness_pct=15)
    if self.now_is_between("sunset - 00:45:00", "sunrise - 03:00:00"):
      self.turn_on("light.porch_light", brightness_pct=20)
      self.turn_on("light.deck_light", brightness_pct=12)
      self.turn_on("switch.deck_steps")

    self.call_service("alarm_control_panel/alarm_disarm", entity_id ="alarm_control_panel.blink_home")
    self.call_service("alarm_control_panel/alarm_disarm", entity_id ="alarm_control_panel.alexa_guard_aab11")
    self.hvac.thermostat_mode({"hmode":"auto"})
    self.livingroom_av.motion_on()
    self.turn_on("switch.hot_water_tank")

  def common_off(self):
    self.log("Turning common lights off")
    self.turn_off("light.attic_lights")
    self.turn_off("light.basement_lights")
    self.turn_off("light.outside_lights")
    self.turn_off("light.office_lights")
    self.turn_off("light.living_room_lights")
    self.turn_off("light.kitchen_lights")
    self.turn_off("light.misc_lights")
    self.turn_off("light.bedroom_lights")

    self.turn_off("switch.fan")
    self.turn_off("switch.kitchen_fan")
    self.turn_off("switch.bathroom_fan")
    self.turn_off("switch.kitchen_speakers")
    self.turn_off("switch.living_room_subwoofer")
    self.turn_off("switch.outdoor_speakers")
    self.turn_off("light.shop_garage_not_lights")


  def cancel_timers(self):
    if "timers" in self.args:
      apps = self.args["timers"].split(",")
      for app in apps:
        App = self.get_app(app)
        App.cancel()

  def force_tv(self,display):
    for x in range(5):
      self.log("force tv {} off".format(display))
      self.call_service("media_player/turn_off", entity_id = display)
      time.sleep(0.5)

  def future_lock(self, kwargs):
    mylocks=kwargs["locks"]
    state=kwargs["state"]
    action="lock/"+kwargs["state"]
    for lock in mylocks:
      self.call_service(action, entity_id = lock)
      self.log("Future lock {} {}".format(lock,action))

  def future_off(self, kwargs):
    myentities=kwargs["myentities"]
    for myentity in myentities:
      self.turn_off(myentity)
      self.log("Future off {}".format(myentity))

  def announce_door_status(self, kwargs):
    garage_door_state_raw = self.get_state("binary_sensor.garage_door_sensor_contact")
    if garage_door_state_raw == "off":
      garage_door_state = "closed"
    elif garage_door_state_raw == "on":
      garage_door_state = "open"

    gdtxt="Garage Door is {}.".format(garage_door_state)
    self.call_service("notify/alexa_media", target = ["media_player.bedroom"], message = gdtxt, data = {"type":"tts"})

    fdtxt="Front Door is {}.".format(self.get_state("lock.lock_fd"))
    self.call_service("notify/alexa_media", target = ["media_player.bedroom"], message = fdtxt, data = {"type":"tts"})

    dtgtxt="Door to the garage is {}.".format(self.get_state("lock.lock_dtg"))
    self.call_service("notify/alexa_media", target = ["media_player.bedroom"], message = dtgtxt, data = {"type":"tts"})
