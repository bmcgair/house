import appdaemon.plugins.hass.hassapi as hass

#
# Args:
# switch: hubitat switch that sets mode via alexa                                        
# temp_sensor: temp sensor on hw return loop

class HotwaterMgr(hass.Hass):

  def initialize(self):
    self.handle = None
    self.hotwater_loop = self.get_app("hotwater_loop")
    self.current_temp = self.get_state("water_heater.water_heater", attribute="temperature")

    self.set_log_level("NOTSET")

    # Subscribe to sensors   
    if "switch" in self.args:
      self.turn_on(self.args["switch"], brightness_pct=1)
      self.turn_on(self.args["switch"], brightness_pct=10)
      self.listen_state(self.switch_event, self.args["switch"], attribute="brightness")

    if "dish_trigger" in self.args:
      self.listen_state(self.dish_trigger, self.args["dish_trigger"])

  def switch_event(self, entity, attribute, old, new, kwargs):
    self.current_temp = self.get_state("water_heater.water_heater", attribute="temperature")
    if new == None:
      new=1
    if old == None:
      old=1

    adjusted = round(new/2.54)
    self.log("Switch: {} Current set temp is: {}".format(adjusted, self.current_temp))
    if old != new:
      if adjusted in range(9,11):
        self.run_in(self.default_temp,0)
      if adjusted in range(19,21):
        self.shower_on()
      if adjusted in range(29,31):
        self.dog_bath_on()
      if adjusted in range(39,41):
        self.dishwasher_on()
      if adjusted in range(49,51):
        self.run_in(self.shower_off, 0)

  def dish_trigger(self, entity, attribute, old, new, kwargs):
    self.log("Received Dishwasher trigger: {}.".format(new))

    if new in ("Closed", "off", "closed", "Off"): 
      self.dishwasher_on()

  def dog_bath_on(self):
    self.cancel()
    self.log("Setting Dog Bath on.")
    self.call_service("water_heater/set_temperature", entity_id = "water_heater.water_heater", temperature = 103)
    self.turn_on("light.bathroom_ceiling_light", brightness_pct=100)
    self.turn_on("light.bathroom_hold", brightness_pct=100)
    self.run_in(self.default_temp, 1800)

  def dishwasher_on(self):
    loop_state = self.get_state("switch.hot_water_loop")
    tankless_state = self.get_state("water_heater.water_heater", attribute="in_use")
    if not tankless_state or (loop_state == "on" and tankless_state == "true"):
      self.call_service("water_heater/set_temperature", entity_id = "water_heater.water_heater", temperature = 140)
      self.turn_on(self.args["switch"], brightness_pct = 40)
      self.log("Tankless is {} Loop is {}. Setting dishwasher mode.".format(tankless_state, loop_state))
    else:
      self.log("Tankless inUse is {}, not setting Dishwasher mode.".format(tankless_state))
    self.run_in(self.default_temp, 5400)

  def shower_on(self):
    self.cancel()
    self.log("Setting Shower on.")
    self.call_service("water_heater/set_temperature", entity_id = "water_heater.water_heater", temperature = 107)
    self.turn_on("light.bathroom_ceiling_light", brightness_pct=80)
    self.turn_on("light.bathroom_hold", brightness_pct=80)
    self.turn_on("switch.bathroom_fan")
    self.run_in(self.shower_off, 1800)

  def shower_off(self, kwargs):
    self.cancel()
    self.log("Setting shower off.")
    self.call_service("water_heater/set_temperature", entity_id = "water_heater.water_heater", temperature = 120)
    self.turn_off("switch.bathroom_fan")
    self.turn_off("light.bathroom_hold")

  def default_temp(self, kwargs):
    self.cancel()
    self.log("Setting default hot water temp: 120.")
    self.call_service("water_heater/set_temperature", entity_id = "water_heater.water_heater", temperature = 120)

  def cancel(self):
    self.cancel_timer(self.handle)
