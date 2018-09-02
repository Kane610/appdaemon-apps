"""Applications that control using remotes."""

import appdaemon.plugins.hass.hassapi as hass

class RemoteControl(hass.Hass):
    """"""

    def initialize(self):
        """"""
        if 'event' in self.args:
            self.listen_event(self.handle_event, self.args['event'])

    def handle_event(self, event_name, data, kwargs):
        """"""
        if data['id'] == self.args['id']:
            self.log(data['event'])
            if data['event'] == 1002:
                self.log('Button on')
            elif data['event'] == 2002:
                self.log('Button dim up')
            elif data['event'] == 3002:
                self.log('Button dim down')
            elif data['event'] == 4002:
                self.log('Button off')

CONF_MAIN_LIGHT = 0
CONF_MAX_BRIGHTNESS = 255
CONF_MIN_BRIGHTNESS = 5

class RemoteControlSelectLight(hass.Hass):
    """Control lights on/off, brightness, together with selecting light to control.

    Designed for deCONZ events.
    Logics are built around the IKEA Trådfri remote control.
    Selecting light with the arrows, selection reset to main light after 30 seconds.
    Arguments:
        remote -- slugified version of entity name.
        light -- List of lights, first light is considered main device.
    """

    def initialize(self):
        """Set up remote and lights."""
        self.remote = self.args.get('remote')
        self.lights = self.args.get('light')

        if not all([self.remote, self.lights]):
            self.log('All configuration parameters are not set')
            return False

        self.event = 'deconz_event'
        self.controlled_light = CONF_MAIN_LIGHT
        self.select_light_handle = None
        self.listen_event(self.handle_event, self.event)

    def handle_event(self, event_name, data, kwargs):
        """Triggers action based on what button event is received.

        1001: Long press power button.
        1002: Short press power button.
        2001: Long press dim up button.
        2002: Short press dim up button.
        3001: Long press dim down button.
        3002: Short press dim down button.
        4001: Long press left arrow.
        4002: Short press left arrow.
        5001: Long press right arrow.
        5002: Short press right arrow.
        """
        if data['id'] == self.remote:

            if data['event'] == 1001:  # Toggle main device on/off
                self.toggle(self.lights[CONF_MAIN_LIGHT])

            elif data['event'] == 1002:  # Toggle select device on/off
                self.toggle(self.lights[self.controlled_light])

            elif data['event'] == 2001:  # Dim up to max
                self.set_brightness(+255)

            elif data['event'] == 2002:  # Dim up 25
                self.set_brightness(+25)

            elif data['event'] == 3001:  # Dim down to min
                self.set_brightness(-255)

            elif data['event'] == 3002:  # Dim down 25
                self.set_brightness(-25)

            elif data['event'] in [4001, 5001]:  # Go back to main device
                self.select_light(0)

            elif data['event'] == 4002:  # Select previous device
                self.select_light(self.controlled_light - 1)

            elif data['event'] == 5002:  # Select next device
                self.select_light(self.controlled_light + 1)

    def set_brightness(self, dim):
        """Set brightness of device.

        If light is off set to maximum or minimum brightness based on button.
        """
        try:
            brightness = self.get_state(
                self.lights[self.controlled_light], attribute='brightness') + dim

        except TypeError:  # If light is off brightness is None
            if dim > 0:
                brightness = CONF_MAX_BRIGHTNESS
            else:
                brightness = CONF_MIN_BRIGHTNESS

        if brightness > CONF_MAX_BRIGHTNESS:
          brightness = CONF_MAX_BRIGHTNESS

        elif brightness < CONF_MIN_BRIGHTNESS:
          brightness = CONF_MIN_BRIGHTNESS

        self.turn_on(self.lights[self.controlled_light], brightness=brightness)

        self.log('Setting brightness to {}'.format(brightness))


    def select_light(self, light_index = CONF_MAIN_LIGHT, flash = True):
        """Select which device to control.

        Feedback to user by doing a single flash of selected light.
        Reverts back to main light after 30 seconds of inactivity.
        """
        light_index = light_index % len(self.lights)

        self.controlled_light = light_index
        if flash:
            self.turn_on(self.lights[self.controlled_light], flash='short')

        if self.select_light_handle:
            self.cancel_timer(self.select_light_handle)

        if self.controlled_light != CONF_MAIN_LIGHT:
            self.select_light_handle = self.run_in(self.set_main_light, 15)

        self.log('Select light {}'.format(self.lights[self.controlled_light]))

    def set_main_light(self, kwargs):
        """Set controlled light back to main light.

        Used by select_device timer to revert to main device.
        """
        self.select_light(flash=False)
