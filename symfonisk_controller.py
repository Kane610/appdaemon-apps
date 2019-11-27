"""Application to use SYMFONISK controller to manage a media player."""

import appdaemon.plugins.hass.hassapi as hass

SINGLE_CLICK = 1002
DOUBLE_CLICK = 1004
TRIPLE_CLICK = 1005

ROTATE_LEFT_START = 2001
ROTATE_LEFT_STOP = 2003
ROTATE_RIGHT_START = 3001
ROTATE_RIGHT_STOP = 3003


class SymfoniskController(hass.Hass):
    """[summary]

    [remote_id] -- [remote id]
    [media_player_entity_id] -- [media player entity id]
    """

    def initialize(self):
        """Set up remotes and lights."""
        self.log(self.args)

        self.remote = self.args["remote"]
        self.media_player = self.args["media_player"]

        self.listen_event(self.handle_event, "deconz_event")

    def handle_event(self, event_name, data, kwargs):
        """Manage deCONZ events."""
        if data['id'] != self.remote:
            return

        self.log("SYMFONISK controller {}".format(data))

        if data['event'] == SINGLE_CLICK:
            self.call_service("media_player/media_play_pause", entity_id=self.media_player)

        elif data['event'] == DOUBLE_CLICK:
            self.call_service("media_player/media_next_track", entity_id=self.media_player)

        elif data['event'] == TRIPLE_CLICK:
            self.call_service("media_player/media_previous_track", entity_id=self.media_player)

        elif data['event'] == ROTATE_LEFT_START:
            # volume = self.get_state(self.media_player)
            self.call_service("media_player/volume_down", entity_id=self.media_player)

        elif data['event'] == ROTATE_LEFT_STOP:
            pass

        elif data['event'] == ROTATE_RIGHT_START:
            self.call_service("media_player/volume_up", entity_id=self.media_player)

        elif data['event'] == ROTATE_RIGHT_STOP:
            pass
