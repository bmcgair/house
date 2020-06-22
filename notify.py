import appdaemon.plugins.hass.hassapi as hass
# Release Notes
##
# Version 1.0:
#   Initial Version

class notify (hass.Hass):

  def pushover(self, **kwargs):
    title=kwargs.get('title') 
    message = kwargs.get('message')
    self.call_service('notify/pushover', title=title, message=message)

  def push_info(self, **kwargs):
    titletxt="INFO " + kwargs.get('title')
    message = kwargs.get('message')
    self.call_service('notify/pushover', title=title, message=message)

  def push_warn(self, **kwargs):
    titletxt="WARN " + kwargs.get['title']
    message = kwargs.get['message']
    self.call_service('notify/pushover', title=title, message=message)

  def push_crit(self, **kwargs):
    titletxt="CRITICAL " + kwargs.get['title']
    message = kwargs.get['message']
    self.call_service('notify/pushover', title=title, message=message)
