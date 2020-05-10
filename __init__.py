import time
from datetime import datetime

from mycroft import MycroftSkill, intent_file_handler
from mycroft.util.time import to_local, now_local, to_system
from alsaaudio import Mixer
from mycroft.audio import wait_while_speaking

__author__ = 'BreziCode'

class QuietHours(MycroftSkill):

    ON_EVENT_NAME = 'quiet_hours_on'
    OFF_EVENT_NAME = 'quiet_hours_off'

    def __init__(self):
        MycroftSkill.__init__(self)
        self.init_settings()
        try:
            self.mixer = Mixer()
        except Exception:
            # Retry instanciating the mixer
            try:
                self.mixer = Mixer()
            except Exception as e:
                self.log.error('Couldn\'t allocate mixer, {}'.format(repr(e)))
                self.mixer = None
        self.saved_volume = self.mixer.getvolume() 

    def initialize(self): 
        self.start_time = None
        self.end_time = None

        self.settings_change_callback = self._init
        self.add_event('private.mycroftai.quiet_hours', self.on_quiet_hours)

        # self._init()

    def _init(self):
        self.clear_events()
        if(self.settings.get('enabled')):
            self.log.info("Quiet hours skill is ENABLED")
            self.log.info("Quiet hours mode is: {}".format(self.settings.get('active')))
            self.log.info("Saved volume is: {}".format(self.saved_volume))
            self.set_start_end()
            self.set_events()
            if(self.should_turn_on_now()):
                self.log.info('Init: truning on because enabled and should')
                self.on()
            elif(self.settings.get('active')):
                self.log.info(
                    'Init: turning off because enabled BUT should not')
                self.off()
        else:
            self.log.info("Quiet hours skill is DISABLED")
            if(self.settings.get('active')):
                self.log.info('Init: turning off because not enabled')
                self.off()
        
    def shutdown(self):
        self.log.info('Shutdown: shutting down')
        self.clear_events()
        if(self.settings.get('active')):
            self.off()           

    def init_settings(self):
        """Add any missing default settings."""
        self.settings.setdefault('enabled', False)
        self.settings.setdefault('start_time_hour', 22)
        self.settings.setdefault('start_time_min', 0)
        self.settings.setdefault('end_time_hour', 8)
        self.settings.setdefault('end_time_min', 0)
        self.settings.setdefault('use_naptime', True)
        self.settings.setdefault('set_volume_to', 0)

        self.settings.setdefault('active', False)

    def on_quiet_hours(self, message):
        self.bus.emit(message.response(
            data={"quiet_hours_on": self.settings.get('active')}))

    def set_start_end(self):
        """ Construct dattime objects from settings for start time and end time """
        now = to_local(datetime.now())
        self.start_time = now.replace(hour=int(self.settings.get('start_time_hour')),
                                      minute=int(self.settings.get('start_time_min')))
        self.log.info("Start time is: {}".format(
            self.start_time.strftime("%H:%M")))
        self.end_time = now.replace(hour=int(self.settings.get('end_time_hour')),
                                    minute=int(self.settings.get('end_time_min')))
        self.log.info("End time is: {}".format(
            self.end_time.strftime("%H:%M")))

    def on(self, speak=True):
        if(not self.settings.get('enabled') or self.mixer is None ):
            return
        self.saved_volume = self.mixer.getvolume()
        self.log.info("Quiet hours are in efect")
        self.settings['active'] = True
        if(speak):
            self.speak_dialog('on')
            wait_while_speaking()
            self.speak_dialog('wake.word')
            wait_while_speaking()
        self.mixer.setvolume(self.settings.get('set_volume_to'))

    def off(self, speak=True):
        if(not self.settings.get('enabled') or self.mixer is None):
            return
        self.mixer.setvolume(self.saved_volume[0])
        self.log.info("Quiet hours not in effect anymore")
        self.settings['active'] = False
        if(speak):
            self.speak_dialog('off')

    def should_turn_on_now(self):
        """ Check if current time is inside teh quiet hours interval"""
        now = now_local()
        self.log.info("Curent time is {}".format(now.strftime("%H:%M")))
        if(self.start_time <= self.end_time):
            self.log.info("Should scenario 1")
            return (self.start_time <= now and now < self.end_time)
        else:
            self.log.info("Should scenario 2")
            return (now > self.start_time or now < self.end_time)

    def clear_events(self):
        self.cancel_scheduled_event(self.ON_EVENT_NAME)
        self.cancel_scheduled_event(self.OFF_EVENT_NAME)

    def set_events(self):
        self.log.info('Setting events')
        self.schedule_repeating_event(self.on, to_system(
            self.start_time), 86400, name=self.ON_EVENT_NAME)
        self.schedule_repeating_event(self.off, to_system(
            self.end_time), 86400, name=self.OFF_EVENT_NAME)

    @intent_file_handler('enable.intent')
    def handle_enable_quiet_hours(self, message):
        if(self.settings.get('enabled')):
            self.speak_dialog('already.enabled')
            return
        self.settings['enabled'] = True
        self.speak_dialog('now.enabled')
        self._init()

    @intent_file_handler('disable.intent')
    def handle_disable_quiet_hours(self, message):
        if(not self.settings.get('enabled')):
            self.speak_dialog('already.disabled')
            return
        self.settings['enabled'] = False
        self.speak_dialog('now.disabled')
        self._init()

    @intent_file_handler('on.intent')
    def handle_activate_quiet_hours(self, message):
        if(not self.settings.get('enabled')):
            self.speak_dialog('disabled')
            return
        self.on()

    @intent_file_handler('off.intent')
    def handle_deactivate_quiet_hours(self, message):
        if(not self.settings.get('enabled')):
            self.speak_dialog('disabled')
            return
        self.off()


def create_skill():
    return QuietHours()
