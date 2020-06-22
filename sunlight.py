import appdaemon.plugins.hass.hassapi as hass
import datetime
                                     
#
# Monitor exterior lux and suggest interior levels accordingly     
# Args:
# Release Notes
#             
# Version 1.1:                                    
                              
class Sunlight(hass.Hass):
                       
  def initialize(self):
    time=datetime.time(0,0,0)
    self.run_minutely(self.illuminance, time)
    self.set_log_level("NOTSET")
    
  def illuminance(self, kwargs):
    # use lux now
    cutoff_mid = float(self.get_state("input_number.cutoff_mid"))
    cutoff_low = float(self.get_state("input_number.cutoff_low"))
    cutoff_west = float(self.get_state("input_number.cutoff_west"))

    # weather
    weather = self.get_state("sensor.darksky_current_icon")
    weather_code = self.get_state("sensor.owm_current_weather_code")
    cloud_coverage = self.get_state("sensor.darksky_current_cloud_coverage")

    east_sunlight = float(self.get_state("sensor.arbor_lodge_solar_rad_lx"))
    west_sunlight = float(self.get_state("sensor.multisensor_deck_illuminance"))                                                        
    self.ambient_level="off"
    self.west_level="high"
    self.east_level="high"
    self.log("East brightness: {} lux".format(east_sunlight))
    self.log("West brightness: {} lux".format(west_sunlight))
    self.log("Cloud Coverage: {}".format(cloud_coverage))
    self.log("Weather Code: {}".format(weather_code))
    self.log("Weather: {}".format(weather))

    # Too complicated and could prob just be done with cloud_coverage and illuminance but whatevs.
    if ((200 <= int(weather_code) <= 699 or int(weather_code) == 804)
      or (weather != "clear-day" and (float(cloud_coverage) >= 85.0))):
      cutoff_low += 10000
      cutoff_mid += 10000
      cutoff_west += 500
      self.log("Cloudy boost")

    elif ((801 <= int(weather_code) <= 804 or 701 <= int(weather_code) <= 799)
      or (weather != "clear-day" and (60.0 <= float(cloud_coverage) <= 84.9))):
      cutoff_low += 8000
      cutoff_mid += 10000
      cutoff_west += 250
      self.log("Med Cloudy boost")

    elif weather != "clear-day" and float(cloud_coverage) <= 59.9:
      cutoff_low += 2500
      cutoff_mid += 5000
      cutoff_west += 100 
      self.log("Med Sunny boost")
    else:
      self.log("Sun no boost")

# East
    if (east_sunlight >= 0 ) and (east_sunlight <= cutoff_low):
      self.ambient_level = "low"
    elif ((east_sunlight > cutoff_low) and (east_sunlight <= cutoff_mid)):
      self.ambient_level = "mid"
    elif (east_sunlight > cutoff_mid):
      self.ambient_level = "high"
    else:
      self.ambient_level = "dark"
    self.log("Outside Light Level: {}".format(self.ambient_level))

# West
    if ((self.ambient_level == "high") and (west_sunlight >= cutoff_west)):
      self.west_level="off"
    elif (("low" or "mid" in self.ambient_level) and (west_sunlight >= cutoff_west)):
      self.west_level="mid"
    elif (( self.ambient_level == "high") and (west_sunlight < cutoff_west)):
      self.west_level="mid"
    elif (("low" or "mid" or "dark" in self.ambient_level) and (west_sunlight < cutoff_west)):
      self.west_level="high"
    self.log("West Lights Setting: {}".format(self.west_level))

# East
    if (self.ambient_level == "high"):
        self.east_level="off"
    elif (self.ambient_level == "mid"):
        self.east_level="mid"
    elif ("low" or "off" in self.ambient_level):
      self.east_level="high"
    self.log("East Lights Setting: {}".format(self.east_level))
