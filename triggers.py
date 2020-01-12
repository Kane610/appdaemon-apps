import appdaemon.plugins.hass.hassapi as hass

#
# Appdaemon test App
#
# Args:
#
# trigger_entity
# enter_state
# exit_state
# action
# target_entity


class instant(hass.Hass):
    def initialize(self):
        self.trigger_entity = self.args.get("trigger_entity", False)
        self.target_entity = self.args.get("target_entity", False)

        self.enter_state = self.args.get("enter_state", False)
        self.exit_state = self.args.get("exit_state", False)

        self.action = self.args.get("action", "off")
        self.handle = self.listen_state(self.trigger, self.trigger_entity)
        self.log("Initialized!")

    def trigger(self, entity, attribute, old, new, kwargs):
        self.log("{} from {} to {}".format(entity, old, new))
        if self.enter_state and not self.exit_state and new == self.enter_state:
            self.call_service(
                "homeassistant/turn_" + self.action, entity_id=self.target_entity
            )
        elif self.exit_state and not self.enter_state and old == self.exit_state:
            self.call_service(
                "homeassistant/turn_" + self.action, entity_id=self.target_entity
            )
        elif (
            self.enter_state
            and self.exit_state
            and old == self.exit_state
            and new == self.enter_state
        ):
            self.call_service(
                "homeassistant/turn_" + self.action, entity_id=self.target_entity
            )

