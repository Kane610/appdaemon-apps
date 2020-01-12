import appdaemon.plugins.hass.hassapi as hass

from enum import IntEnum
import json

#
# Hello World App
#
# Args:
#


class Context(IntEnum):
    force_majeur = 5
    unknown_trigger = 4
    manual_override = 3
    automatic_trigger = 2
    scheduled_trigger = 1
    initial_state = 0


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

        self.run_daily(self._reset_control, self.parse_time(TIME_RESET_CONTROL))
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

    def _reset_control(self):
        """Reset manual override control."""
        for light in self.lights:
            light.reset_context()


class Light:
    def __init__(self, light: dict, appdaemon: Lights) -> None:
        self.raw = light
        self.appdaemon = appdaemon
        self._attributes = light.get("attributes", {})
        self._context = Context.initial_state
        self._snapshot = {}

        self.appdaemon.listen_state(self.update, self.entity_id)

    def update(self, entity, attribute, old, new, kwargs) -> None:
        self.raw = self.appdaemon.get_state(entity=self.entity_id, attribute="all")

        if new == "on":
            self._attributes = self.raw["attributes"]

    def reset_context(self) -> None:
        self._context = Context.initial_state

    def evaluate_context(self, context: IntEnum) -> bool:
        """Evaluate if context is ok to pass."""
        if context < self._context:
            self.appdaemon.log(
                "Light controlled on higher prio {context} < {self.context}"
            )
            return False
        return True

    def call_service(
        self,
        service: str,
        context: IntEnum,
        brightness: int = None,
        color_temp: int = None,
        flash: str = None,
    ) -> None:

        print(f"{self.entity_id} {self.state}, {service} {context}>={self._context}")
        if self.state != "off" and not self.evaluate_context(context):
            self.appdaemon.log(f"{self.entity_id} not allowed to change")
            return

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
        self._context = context

    def turn_on(self, context: IntEnum, **kwargs) -> None:
        self.call_service("turn_on", context, **kwargs)

    def turn_off(self, context: IntEnum, **kwargs) -> None:
        self.call_service("turn_off", context, **kwargs)

    def flash(self) -> None:
        self.call_service("turn_on", self._context, flash="short")

    def store_state(self, context: IntEnum) -> None:
        if not self.evaluate_context(context):
            return

        if self.state not in ("on", "off"):
            self.appdaemon.log("Light in bad state {self.state}")
            return

        self._snapshot = {
            "state": self.state,
            "context": self._context,
            "brightness": self.attributes.get("brightness"),
            "color_temp": self.attributes.get("color_temp"),
        }

    def restore_state(self, context: IntEnum) -> None:
        if not self.evaluate_context(context):
            return

        if not self._snapshot:
            self.appdaemon.log("Snapshot empty")
            return

        self._context = self._snapshot.pop("context")
        self.call_service(
            f'turn_{self._snapshot.pop("state")}',
            self._context,
            brightness=self._snapshot.pop("brightness"),
            color_temp=self._snapshot.pop("color_temp"),
        )

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
        return f"{json.dumps(self.raw)}, light context: {self._context}"

    def __str__(self) -> str:
        return f"{self.entity_id} {self.state}"
