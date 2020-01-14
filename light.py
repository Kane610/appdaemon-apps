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

TIME_RESET_CONTROL = "04:00:00"

CONFIGURED_TIME_WINDOWS_OF_LIGHTING_SCENE = {
    "05:00:00": {"brightness": 100, "ambience": 50},
    "10:00:00": {"brightness": 255, "ambience": 30},
}


class Lights(hass.Hass):
    def initialize(self) -> None:
        lights = self.get_state("light")
        self.lights = {
            entity_id: Light(light, self) for entity_id, light in lights.items()
        }

        self.log("Initialized")

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
        self._attributes = light.get("attributes", {})
        self._snapshot = None

        self.appdaemon.listen_state(self.update, self.entity_id)

    def update(self, entity, attribute, old, new, kwargs) -> None:
        self.raw = self.appdaemon.get_state(entity_id=self.entity_id, attribute="all")

        if new == "on":
            self._attributes = self.raw["attributes"]

    def call_service(
        self,
        service: str,
        brightness: int = None,
        color_temp: int = None,
        flash: str = None,
    ) -> None:
        print(f"{self.entity_id} {self.state}, {service}")
        kwargs = {}

        if service != "turn_off":
            if brightness:
                kwargs["brightness"] = brightness

            if color_temp:
                kwargs["color_temp"] = color_temp

            if flash:
                kwargs["flash"] = flash

        self.appdaemon.call_service(
            f"light/{service}", entity_id=self.entity_id, **kwargs
        )

    def turn_on(self, **kwargs) -> None:
        self.call_service("turn_on", **kwargs)

    def turn_off(self, **kwargs) -> None:
        self.call_service("turn_off", **kwargs)

    def flash(self) -> None:
        self.call_service("turn_on", flash="short")

    def store_state(self, delay: int) -> None:
        if self.state not in ("on", "off"):
            self.appdaemon.log("Light in bad state {self.state}")
            return

        snapshot_data = {
            "state": self.state,
            "brightness": self.attributes.get("brightness"),
            "color_temp": self.attributes.get("color_temp"),
        }
        target_time = datetime.now() + timedelta(seconds=delay)
        if self._snapshot and self._snapshot < target_time:
            snapshot_data = self._snapshot.data
        self._snapshot = snapshot(snapshot_data, target_time)

    def restore_state(self) -> None:
        self.call_service(
            f'turn_{self._snapshot.data["state"]}',
            brightness=self._snapshot.data["brightness"],
            color_temp=self._snapshot.data["color_temp"],
        )
        self._snapshot = None

    def clear_snapshot(self) -> None:
        self._snapshot = None

    @property
    def entity_id(self) -> str:
        return self.raw["entity_id"]

    @property
    def state(self) -> str:
        return self.raw["state"]

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
    def __init__(self, data: object, target_time: datetime) -> bool:
        print(data, target_time)
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

