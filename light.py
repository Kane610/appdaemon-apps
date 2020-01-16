import appdaemon.plugins.hass.hassapi as hass

from datetime import datetime, timedelta
import json

#
# Hello World App
#
# Args:
#


# context -> operational_state
# Normal, temporary override, manual override
#
# store with time stamp
# store original state?
# motion detection - on and restore a set or accumulated amount of time
# play movie - on and restore during play/pause/done
# allow restoring to original state?

ATTR_ATTRIBUTES = "attributes"
ATTR_BRIGHTNESS = "brightness"
ATTR_COLOR_TEMP = "color_temp"
ATTR_FLASH = "flash"
ATTR_FLASH_SHORT = "short"
ATTR_STATE = "state"
ATTR_TURN_OFF = "turn_off"
ATTR_TURN_ON = "turn_on"

TIME_RESET_CONTROL = "04:00:00"

CONFIGURED_TIME_WINDOWS_OF_LIGHTING_SCENE = {
    "05:00:00": {ATTR_BRIGHTNESS: 100, ATTR_COLOR_TEMP: 50},
    "10:00:00": {ATTR_BRIGHTNESS: 255, ATTR_COLOR_TEMP: 30},
    "21:37:30": {ATTR_BRIGHTNESS: 255, ATTR_COLOR_TEMP: 30},
}


class Lights(hass.Hass):
    def initialize(self) -> None:
        lights = self.get_state("light")
        self.lights = {
            entity_id: Light(light, self) for entity_id, light in lights.items()
        }

        # for time, kwargs in CONFIGURED_TIME_WINDOWS_OF_LIGHTING_SCENE.items():
        #     self.run_daily(self.circadian_time, time, **kwargs)

        self.log("Initialized")

    def circadian_time(self, kwargs):
        # print("CIRCADIAN", kwargs)
        pass

    def get(self, *, entity_id: str = None, entity_ids: list = None) -> dict:
        if entity_id:
            entity_ids = [entity_id]

        if entity_ids:
            return {
                entity_id: light
                for entity_id, light in self.lights.items()
                if entity_id in entity_ids
            }

        return dict(self.lights)


class Light:
    def __init__(self, light: dict, appdaemon: Lights) -> None:
        self.raw = light
        self.appdaemon = appdaemon
        self._attributes = light.get(ATTR_ATTRIBUTES, {})
        self._snapshot = None

        self.appdaemon.listen_state(self.update, self.entity_id)

    def update(self, entity, attribute, old, new, kwargs) -> None:
        self.raw = self.appdaemon.get_state(entity_id=self.entity_id, attribute="all")

        if new == "on":
            self._attributes = self.raw[ATTR_ATTRIBUTES]

    def call_service(
        self,
        service: str,
        brightness: int = None,
        color_temp: int = None,
        flash: str = None,
    ) -> None:
        print(f"{self.entity_id} {self.state}, {service}")
        kwargs = {}

        if service != ATTR_TURN_OFF:
            if brightness:
                kwargs[ATTR_BRIGHTNESS] = brightness

            if color_temp:
                kwargs[ATTR_COLOR_TEMP] = color_temp

            if flash:
                kwargs[ATTR_FLASH] = flash

        self.appdaemon.call_service(
            f"light/{service}", entity_id=self.entity_id, **kwargs
        )

    def turn_on(self, **kwargs) -> None:
        self.call_service(ATTR_TURN_ON, **kwargs)

    def turn_off(self, **kwargs) -> None:
        self.call_service(ATTR_TURN_OFF, **kwargs)

    def flash(self) -> None:
        self.call_service(ATTR_TURN_ON, flash=ATTR_FLASH_SHORT)

    def toggle(self, **kwargs) -> None:
        self.appdaemon.toggle(entity_id=self.entity_id, **kwargs)

    def store_state(self, app_name: str, delay: int) -> None:
        if self.state not in ("on", "off"):
            self.appdaemon.log("Light in bad state {self.state}")
            return

        snapshot_data = {
            ATTR_STATE: self.state,
            ATTR_BRIGHTNESS: self.attributes.get(ATTR_BRIGHTNESS),
            ATTR_COLOR_TEMP: self.attributes.get(ATTR_COLOR_TEMP),
        }
        target_time = datetime.now() + timedelta(seconds=delay)
        if self._snapshot and self._snapshot < target_time:
            snapshot_data = self._snapshot.data
        self._snapshot = snapshot(app_name, snapshot_data, target_time)

    def restore_state(self, app_name: str) -> None:
        if self._snapshot.app_name == app_name:
            self.call_service(
                f"turn_{self._snapshot.data[ATTR_STATE]}",
                brightness=self._snapshot.data[ATTR_BRIGHTNESS],
                color_temp=self._snapshot.data[ATTR_COLOR_TEMP],
            )
            self._snapshot = None

    def clear_snapshot(self) -> None:
        self._snapshot = None

    @property
    def entity_id(self) -> str:
        return self.raw["entity_id"]

    @property
    def state(self) -> str:
        return self.raw[ATTR_STATE]

    @property
    def attributes(self) -> dict:
        return self._attributes

    @property
    def context(self) -> dict:
        return self.raw["context"]

    @property
    def last_changed(self) -> str:
        return self.raw["last_changed"]

    @property
    def last_updated(self) -> str:
        return self.raw["last_updated"]

    def __repr__(self) -> str:
        return f"{json.dumps(self.raw)}"

    def __str__(self) -> str:
        return f"{self.entity_id} {self.state}"


class snapshot:
    def __init__(self, app_name: str, data: object, target_time: datetime) -> bool:
        self.app_name = app_name
        self.data = data
        self._target_time = target_time

    def __eq__(self, other: datetime) -> bool:
        return self._target_time == other

    def __lt__(self, other: datetime) -> bool:
        return self._target_time < other


# class snapshot_manager:
#     def __init__(self):
#         self._snapshots = {}

#     def store(self, id: str, data: object, target_time: datetime) -> None:
#         if id in self._snapshots and self._snapshot[id] < target_time:
#             data = self._snapshot[id].data
#         self._snapshots[id] = snapshot(data, target_time)

#     def restore(self, id: str) -> object:
#         if not self._snapshots:
#             return

#         if len(self._snapshots) == 1:
#             return self._snapshots.pop(id).data

#         snapshot = self._snapshots.pop(id)

#         data = snapshot.data
#         for item in self._snapshots.values():
#             if snapshot < item:
#                 next_data = item.data
#                 item.data = data
#                 data = next_data

#     def remove(self, id: str) -> None:
#         try:
#             del self._snapshots[id]
#         except KeyError:
#             pass


# https://docs.python.org/3/reference/datamodel.html#emulating-container-types

