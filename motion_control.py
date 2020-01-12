"""Applications that are triggered by motion."""

import appdaemon.plugins.hass.hassapi as hass

from light import Context


class MotionControlLights(hass.Hass):
    """Motion control lights.

    Will not modify lights that are already on.
    Will not turn off lights that have been modified after motion trigger.
    Arguments:
        delay {int} -- Time [s] before turning lights back off, default is 90.
        sensor {string} -- Binary sensor that will trigger lights to go on.
        lights {list} -- Light entity ids, first light is main light.
        lightlevel {dict} -- Keys is max light level and value is sensor
    """

    def initialize(self):
        """Set up delay, sensor and lights"""
        if "light" not in self.args and "sensor" not in self.args:
            self.log("All configuration parameters are not set")
            return False

        self.delay = self.args.get("delay", 90)
        self.lightlevel = self.args.get("lightlevel", {})

        light_master = self.get_app("light_master")
        self.lights = light_master.get(entity_ids=self.args["light"])

        self.restore_light_handle = None
        self.listen_state(self.motion, self.args["sensor"])

        # self.motion("test", "", "off", "on", "")

        self.log("Initialized")

    def motion(self, entity, attribute, old, new, kwargs):
        """"""
        if new == "on":
            self.log(f"{entity} triggered")

            if self.within_limits():  # Motion is already active
                self.light_on()

            if self.restore_light_handle is not None:
                self.cancel_timer(self.restore_light_handle)

            self.restore_light_handle = self.run_in(self.restore, self.delay)

    def light_on(self):
        """Turn lights on."""
        for light in self.lights.values():
            light.store_state(Context.automatic_trigger)
            light.turn_on(Context.automatic_trigger)

    def restore(self, kwargs):
        """Restore lights."""
        for light in self.lights.values():
            light.restore_state(Context.automatic_trigger)

    def within_limits(self):
        """Check that light level sensors are within limits."""
        within_limit = True

        for lux_sensor, limit in self.lightlevel.items():
            current_lightlevel = float(self.get_state(lux_sensor))
            if current_lightlevel > limit:
                within_limit = False
                self.log("Light level beyond limit")
                break

        return within_limit
