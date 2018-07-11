"""Applications that are triggered by motion."""

import appdaemon.plugins.hass.hassapi as hass


class MotionControlLights(hass.Hass):
    """Motion control lights.

    Will not modify lights that are already on.
    Will not turn off lights that have been modified after motion trigger.
    Arguments:
        delay {int} -- Time [s] before turning lights back off, default is 90.
        sensor {string} -- Binary sensor that will trigger lights to go on.
        lights {list} -- List of lights entity ids.
    """


    def initialize(self):
        """Set up delay, sensor and lights"""
        self.delay = self.args.get('delay', 90)
        self.sensor = self.args.get('sensor')
        self.lights = self.args.get('light')
        if not all([self.sensor, self.lights]):
            self.log('All configuration parameters are not set')
            return False
        self.lights_to_turn_off = []
        self.light_off_handle = None
        self.light_override_handle = {}
        self.listen_state(self.motion, self.sensor)

    def motion(self, entity, attribute, old, new, kwargs):
        """"""
        if new == 'on':
            self.log("{} triggered".format(entity))
            if not self.lights_to_turn_off:  # Motion is already active
                self.light_on()
            if self.light_off_handle is not None:
                self.cancel_timer(self.light_off_handle)
            if self.lights_to_turn_off:  # Don't run lights off if no lights to turn off
                self.light_off_handle = self.run_in(self.light_off, self.delay)

    def light_on(self):
        """Turn lights on.

        Store which lights where turned on.
        """
        for light in self.lights:
            state = self.get_state(light)
            if state == 'off':
                self.lights_to_turn_off.append(light)
                self.turn_on(light)
        self.log("Turning on {}".format(self.lights_to_turn_off))

    def light_off(self, kwargs):
        """Turn lights off.

        Only turn lights off which hasn't been changed after motion turned it on.
        """
        for light in self.lights_to_turn_off:
            last_updated = self.get_state(light, attribute='last_updated')  # Any change
            last_changed = self.get_state(light, attribute='last_changed')  # State change
            if last_changed == last_updated:
                self.log('Turning off {}'.format(light))
                self.turn_off(light)
        self.lights_to_turn_off = []
