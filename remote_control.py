"""Applications that control using remotes."""

import appdaemon.plugins.hass.hassapi as hass

CONF_MAIN_DEVICE = 0
CONF_MAX_BRIGHTNESS = 255
CONF_MIN_BRIGHTNESS = 5

BUTTON_PRESS = 0
BUTTON_RELEASE = 2
BUTTON_LONG_PRESS = 1
BUTTON_LONG_RELEASE = 3


class RemoteControl(RemoteControlBase):
    """"""

    def initialize(self):
        """"""
        self.lights = ['light.ambience_spot_5']
        super().initialize()

    def handle_button_event(self):
        """"""
        if self.button_event == 1002:
            self.log('Button on')
        elif self.button_event == 2002:
            self.log('Button dim up')
        elif self.button_event == 3002:
            self.log('Button dim down')
        elif self.button_event == 4002:
            self.log('Button off')


class HueDimmer(RemoteControlBase):
    """Example config.

remote_control_living_room:
  module: remote_control
  class: HueDimmer
  remotes:
    - dimmer_switch_5
  long_press:
    1:
      - light.ambience_spot_1
      - light.ambience_spot_2
    3:
      - light.ambience_spot_5
      - light.ambience_spot_6
  multi_click:
    1:
      - light.ambience_spot_1
      - light.ambience_spot_2
    2:
      - light.ambience_spot_5
      - light.ambience_spot_6
    3:
      - light.ambience_spot_8
      - light.ambience_spot_9
    """

    POWER_ON = 1000
    DIM_UP = 2000
    DIM_DOWN = 3000
    POWER_OFF = 4000

    # MAPPING = {
    #     1
    # }
    # def initialize(self):
    #     """"""
    #     super().initialize()

    def handle_button_event(self):
        """"""
        self.log('HANDLE BUTTON EVENT')
        button_event = self.button_event

        if button_event == self.POWER_ON + BUTTON_PRESS:
            self.log('POWER ON PRESSED')
        elif button_event == self.POWER_ON + BUTTON_RELEASE:
            self.log('POWER ON RELEASED, check multi click')
            self.turn_multi_click('on')
        elif button_event == self.POWER_ON + BUTTON_LONG_PRESS:
            self.log('POWER ON LONG PRESS, check long press')
            self.turn_long_press('on')
        elif button_event == self.POWER_ON + BUTTON_LONG_RELEASE:
            self.log('POWER ON LONG RELEASE')

        elif button_event == self.DIM_UP + BUTTON_PRESS:
            self.log('DIM UP PRESSED')
        elif button_event == self.DIM_UP + BUTTON_RELEASE:
            self.log('DIM UP RELEASED, check multi click')
        elif button_event == self.DIM_UP + BUTTON_LONG_PRESS:
            self.log('DIM UP LONG PRESS, check long press')
        elif button_event == self.DIM_UP + BUTTON_LONG_RELEASE:
            self.log('DIM UP LONG RELEASE')

        elif button_event == self.DIM_DOWN + BUTTON_PRESS:
            self.log('DIM DOWN PRESSED')
        elif button_event == self.DIM_DOWN + BUTTON_RELEASE:
            self.log('DIM DOWN RELEASED, check multi click')
        elif button_event == self.DIM_DOWN + BUTTON_LONG_PRESS:
            self.log('DIM DOWN LONG PRESS, check long press')
        elif button_event == self.DIM_DOWN + BUTTON_LONG_RELEASE:
            self.log('DIM DOWN LONG RELEASE')

        elif button_event == self.POWER_OFF + BUTTON_PRESS:
            self.log('POWER OFF PRESSED')
        elif button_event == self.POWER_OFF + BUTTON_RELEASE:
            self.log('POWER OFF, check multi click')
            self.turn_multi_click('off')
        elif button_event == self.POWER_OFF + BUTTON_LONG_PRESS:
            self.log('POWER OFF PRESS, check long press')
            self.turn_long_press('off')
        elif button_event == self.POWER_OFF + BUTTON_LONG_RELEASE:
            self.log('POWER OFF LONG RELEASE')


class RemoteControlSecondary(RemoteControlBase):
    """Secondary control to a Zigbee group.

    Logics are built around the Hue Dimmer remote control.
    Control second group of lights with long press.
    Arguments:
        remote -- slugified version of entity name.
        light -- List of lights, first light is considered main device.
    """

    def handle_button_event(self):
        """"""
        if self.button_event == 1001:
            self.turn_devices('on')

        elif self.button_event in [2000, 2001]:
            self.set_brightness(+40)

        elif self.button_event in [3000, 3001]:
            self.set_brightness(-40)

        elif self.button_event == 4001:
            self.turn_devices("off")


class RemoteControlSelectLight(RemoteControlBase):
    """Control lights on/off, brightness, together with selecting light to control.

    Logics are built around the IKEA Trådfri remote control.
    Selecting light with the arrows, selection reset to main light after 30 seconds.
    Arguments:
        remote -- slugified version of entity name.
        light -- List of lights, first light is considered main device.
    """

    def handle_button_event(self):
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

        if self.button_event == 1001:  # Toggle main device on/off
            self.toggle(self.lights[CONF_MAIN_DEVICE])

        elif self.button_event == 1002:  # Toggle select device on/off
            self.toggle(self.controlled_device)

        elif self.button_event == 2001:  # Dim up to max
            self.set_brightness_controlled_light(+255)

        elif self.button_event == 2002:  # Dim up 25
            self.set_brightness_controlled_light(+25)

        elif self.button_event == 3001:  # Dim down to min
            self.set_brightness_controlled_light(-255)

        elif self.button_event == 3002:  # Dim down 25
            self.set_brightness_controlled_light(-25)

        elif self.button_event in [4001, 5001]:  # Go back to main device
            self.select_main_device()

        elif self.button_event == 4002:  # Select previous device
            self.select_previous_device()

        elif self.button_event == 5002:  # Select next device
            self.select_next_device()




class RemoteControlBase(hass.Hass):
    """[summary]

    Returns:
        [type] -- [description]
    """

    def initialize(self):
        """Set up remotes and lights."""
        self.log(self.args)

        self.lights = self.args.get('light', True)
        self.long_press = self.args.get('long_press')
        self.multi_click = self.args.get('multi_click')

        self.remotes = self.args.get('remotes')
        if not self.remotes:
            self.remotes = [self.args.get('remote')]

        self.controlled_device_index = CONF_MAIN_DEVICE
        self.select_device_handle = None

        self.event = 'deconz_event'
        self.listen_event(self.handle_event, self.event)

        self.button_event = None
        self.button_timer = None
        self.button_counters = {}

    def handle_event(self, event_name, data, kwargs):
        """"""
        remote_id = data['id']
        if remote_id in self.remotes:
            self.log(data)
            # use button_event / 1000 to check if it is the same button, else reset
            self.button_event = data['event']

            if self.button_event not in self.button_counters:
                self.button_counters[self.button_event] = 0
            self.button_counters[self.button_event] += 1

            self.log('Button event {}'.format(self.button_counters))

            if self.button_timer:
                self.cancel_timer(self.button_timer)
            self.button_timer = self.run_in(self.reset_button_data, 5)

            self.handle_button_event()

    def handle_button_event(self):
        """"""
        raise NotImplementedError

    def reset_button_data(self, kwargs=None):
        """"""
        self.log("Reseting counter for {}".format(self.button_counters))
        self.button_event = None
        self.button_counters = {}

    def turn_long_press(self, action):
        """"""
        #self.log("TURN LONG PRESS {} {}".format(self.button_counters, self.long_press))
        button_counter = self.button_counters[self.button_event]
        if not button_counter in self.long_press:
            return

        for device in self.long_press[button_counter]:
            self.call_service('homeassistant/turn_'+action, entity_id=device)
        self.log("Turn {action} device {device}".format(
            action=action, device=self.long_press[button_counter]))

    def turn_multi_click(self, action):
        """"""
        #self.log("TURN LONG PRESS {} {}".format(self.button_counters, self.long_press))
        button_counter = self.button_counters[self.button_event]
        if not button_counter in self.multi_click:
            return

        for device in self.multi_click[button_counter]:
            self.call_service('homeassistant/turn_'+action, entity_id=device)
        self.log("Turn {action} device {device}".format(
            action=action, device=self.multi_click[button_counter]))

### Control state ###

    def turn_devices(self, action):
        """Turn on or off device."""
        for device in self.lights:
            self.call_service('homeassistant/turn_'+action, entity_id=device)
        self.log("Turn {action} device {device}".format(
            action=action, device=self.lights))

### Control brightness ###

    def set_brightness_controlled_light(self, dim):
        """Set brightness of device."""
        self.set_brightness(self.controlled_device, dim)

    def set_brightness_all_lights(self, dim):
        """Set brightness of all devices."""
        for light in self.lights:
            self.set_brightness(light, dim)

    def set_brightness(self, light, dim):
        """Set brightness of device.

        If light is off set to maximum or minimum brightness based on button.
        """
        try:
            brightness = self.get_state(light, attribute='brightness') + dim

        except TypeError:  # If light is off brightness is None
            if dim > 0:
                brightness = CONF_MAX_BRIGHTNESS
            else:
                brightness = CONF_MIN_BRIGHTNESS

        if brightness > CONF_MAX_BRIGHTNESS:
          brightness = CONF_MAX_BRIGHTNESS

        elif brightness < CONF_MIN_BRIGHTNESS:
          brightness = CONF_MIN_BRIGHTNESS

        self.turn_on(light, brightness=brightness)

        self.log("Setting brightness to {}".format(brightness))

### Select device logic ###

    @property
    def controlled_device(self):
        """"""
        return self.lights[self.controlled_device_index]

    def select_device(self, device_index, flash=True):
        """Select which device to control.

        Feedback to user by doing a single flash of selected device.
        Reverts back to main device after 30 seconds of inactivity.
        """
        self.controlled_device_index = device_index % len(self.lights)

        if flash and self.controlled_device.startswith('light.'):
            self.turn_on(self.controlled_device, flash='short')

        if self.select_device_handle:
            self.cancel_timer(self.select_device_handle)

        if self.controlled_device_index != CONF_MAIN_DEVICE:
            self.select_device_handle = self.run_in(self.select_main_device, 15)

        self.log("Select light {}".format(self.controlled_device))

    def select_main_device(self, kwargs):
        """Turn controls back to main device.

        Used by select_device timer to revert to main device.
        """
        self.select_device(CONF_MAIN_DEVICE, flash=False)

    def select_next_device(self):
        """Set controlled device to next in list."""
        self.select_device(self.controlled_device_index + 1)

    def select_previous_device(self):
        """Set controlled device to previous in list."""
        self.select_device(self.controlled_device_index - 1)
