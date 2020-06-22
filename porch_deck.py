import appdaemon.plugins.hass.hassapi as hass

class PorchAndDeck(hass.Hass):

  def initialize(self):
    self.run_at_sunset(self.light_onfunction,offset = int(self.args["sunset_offset"]))

  def light_onfunction (self, kwargs):
      self.turn_on("light.porch_light", brightness_pct=40)
      self.turn_on("light.deck_light", brightness_pct=12)
      self.turn_on("switch.deck_steps")

  def light_offunction (self, kwargs):
      self.turn_off("light.porch_light")
      self.turn_off("light.deck_light")
      self.turn_off("switch.deck_steps")
