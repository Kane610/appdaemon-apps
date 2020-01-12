import appdaemon.plugins.hass.hassapi as hass

from light import Context

###
# Appdaemon light schedules App
#
# Schedules lights for on and off switching,
# also allows off switch to be overridden by sensor
#
# Args:
#
# time: ', ' separated list with one or more time and action
#   example: time = 05:00:00 on, sunrise off
# light: ', ' separated list with one or more light entity_id
#   example: light = light.lamp1, light.lamp2
# group: ', ' separated list with one or more group containing light
#   example: group = group.lightgroup1, group.lightgroup2
# sensor: single sensor that can delay schedule when turning off
#
# Note: takes inspiration from AppDaemon motion detectionlights


class lighting(hass.Hass):
    def initialize(self):
        if "time" not in self.args:
            self.log("No time attribute configured")
            return False

        light_master = self.get_app("light_master")

        if "light" in self.args:
            self.lights = light_master.get(entity_ids=self.args["light"])
        else:
            self.lights = light_master.get()

        self.log(f"{self.lights.keys()}")

        for time, action in self.args["time"].items():
            time = self.parse_time(time)
            self.run_daily(
                self.schedule_callback, time, action=action, trigger="schedule"
            )

        self.sensors = self.args.get("sensor")
        self.sensor_active = False
        self.sensor_activity_handle = None
        self.schedule_active = False

        # self.schedule_callback({"action": "on", "trigger": "asdad"})

        self.log("Initialized")

    def schedule_callback(self, kwargs):
        action = kwargs["action"]
        trigger = kwargs["trigger"]

        if self.sensors and not self.sensor(action, trigger):
            return

        for light in self.lights.values():
            light.call_service(f"turn_{action}", Context.scheduled_trigger)

        self.log("Turned {} {}".format(action, self.lights))

    ###############################################################################
    #
    # Sensor functions
    #

    # Sensor is set up to listen when action equals on
    # Sensor will stop listen on two different situations
    #   1. Sensor is low and schedule has triggered
    #   2. Sensor is low after schedule has triggered
    def sensor(self, action, trigger):
        if action == "on":
            self.sensor_activity_handle = self.listen_state(
                self.sensor_activity, self.sensors
            )
            self.log("Listening on sensor {}".format(self.sensors))
            self.schedule_active = True
        elif action == "off":
            # Schedule is still active, sensor is not allowed to turn off light
            if trigger == "sensor" and self.schedule_active:
                self.sensor_active = False
                self.log("Sensor tried to turn off light with schedule active")
                return False
            # Schedule has triggered and sensor is active,
            # sensor is now responsible for turning off light
            elif trigger == "schedule" and self.sensor_active:
                self.schedule_active = False
                self.log("Sensor is now allowed to turn off lights")
                return False
            # Everything is ready to turn off
            else:
                self.cancel_listen_state(self.sensor_activity_handle)
                self.schedule_active = False
                self.sensor_active = False
        return True

    # Triggers on sensor activity
    def sensor_activity(self, entity, attribute, old, new, kwargs):
        self.log(f"{entity}, {attribute}, {old}, {new}, {kwargs}")
        if old == new and self.sensor_active:
            return False
        self.log("Sensor {} changed state from  {}".format(entity, new))
        if self.sensor_active:
            self.cancel_timer(self.sensor_active)
        if new == "idle":
            self.sensor_active = self.run_in(
                self.run_daily_callback, 450, action="off", trigger="sensor"
            )
        else:
            self.sensor_active = True
