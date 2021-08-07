import re
import subprocess
import time

from dearpygui import dearpygui as dpg

WIDTH = 380
HEIGHT = 500


class Widgets:
    gamma_slider_r = dpg.generate_uuid()
    gamma_slider_g = dpg.generate_uuid()
    gamma_slider_b = dpg.generate_uuid()
    brightness_slider = dpg.generate_uuid()
    color_picker = dpg.generate_uuid()


class Config:
    brightness = 1
    gamma_r = 1
    gamma_g = 1
    gamma_b = 1
    color_picker = [255, 255, 255, 255]
    _result = subprocess.run(["xrandr", "--listactivemonitors"], capture_output=True)
    monitors = {
        name[1]: False for name in re.findall(r"(\d).*  (.+)", _result.stdout.decode())
    }
    _latest_run = 0

    @classmethod
    def reset(cls):
        cls.brightness = 1
        cls.gamma_r = 1
        cls.gamma_g = 1
        cls.gamma_b = 1
        cls.color_picker = [255, 255, 255, 255]

        dpg.set_value(Widgets.gamma_slider_r, cls.gamma_r)
        dpg.set_value(Widgets.gamma_slider_g, cls.gamma_g)
        dpg.set_value(Widgets.gamma_slider_b, cls.gamma_b)
        dpg.set_value(Widgets.brightness_slider, cls.brightness)
        dpg.set_value(Widgets.color_picker, cls.color_picker)
        cls.run_command(include_all_monitors=True)

    @classmethod
    def run_command(cls, include_all_monitors=False):
        # Prevent flooding with commands
        if time.time() - cls._latest_run < 0.01:
            return

        # Prevent black screen
        if sum([cls.gamma_r, cls.gamma_g, cls.gamma_b]) < 0.15:
            return

        for monitor, enabled in cls.monitors.items():
            if not include_all_monitors and not enabled:
                continue
            subprocess.run(
                [
                    "xrandr",
                    "--output",
                    monitor,
                    "--brightness",
                    str(cls.brightness),
                    "--gamma",
                    f"{cls.gamma_r}:{cls.gamma_g}:{cls.gamma_b}",
                ]
            )

        cls._latest_run = time.time()

    @classmethod
    def select_monitor_callback(cls, sender):
        monitor = dpg.get_item_label(sender)
        cls.monitors[monitor] = dpg.get_value(sender)
        cls.run_command()

    @classmethod
    def gamma_slider_callback(cls, sender: int, color: int):
        value: float = dpg.get_value(sender)
        if color == 0:
            cls.gamma_r = value
        elif color == 1:
            cls.gamma_g = value
        elif color == 2:
            cls.gamma_b = value
        else:
            raise ValueError("Invalid color: not one of [0, 1, 2]")

        cls.run_command()

    @classmethod
    def brightness_slider_callback(cls):
        cls.brightness = dpg.get_value(Widgets.brightness_slider)
        cls.run_command()

    @classmethod
    def color_picker_callback(cls):
        rgb = dpg.get_value(Widgets.color_picker)

        normalized_rgb = [c / 255 for c in rgb]
        cls.gamma_r = normalized_rgb[0] or 0.001
        cls.gamma_g = normalized_rgb[1] or 0.001
        cls.gamma_b = normalized_rgb[2] or 0.001

        dpg.set_value(Widgets.gamma_slider_r, cls.gamma_r)
        dpg.set_value(Widgets.gamma_slider_g, cls.gamma_g)
        dpg.set_value(Widgets.gamma_slider_b, cls.gamma_b)
        cls.run_command()


def main():
    with dpg.window(width=WIDTH, height=HEIGHT) as main_window:
        with dpg.handler_registry():
            dpg.add_key_press_handler(key=82, callback=Config.reset)

        dpg.add_button(label="Reset all", width=90, height=30, callback=Config.reset)
        dpg.add_same_line()
        dpg.add_text('Press "R" to reset all!')

        for monitor_name in Config.monitors:
            dpg.add_checkbox(
                label=monitor_name,
                callback=lambda sender: Config.select_monitor_callback(sender),
            )

        dpg.add_slider_float(
            label="Brightness",
            id=Widgets.brightness_slider,
            min_value=0.1,
            max_value=2,
            callback=Config.brightness_slider_callback,
            default_value=Config.brightness,
        )
        dpg.add_slider_float(
            label="Gamma red",
            id=Widgets.gamma_slider_r,
            min_value=0.001,
            max_value=2,
            callback=lambda sender: Config.gamma_slider_callback(sender, 0),
            default_value=Config.gamma_r,
        )
        dpg.add_slider_float(
            label="Gamma green",
            id=Widgets.gamma_slider_g,
            min_value=0.001,
            max_value=2,
            callback=lambda sender: Config.gamma_slider_callback(sender, 1),
            default_value=Config.gamma_g,
        )
        dpg.add_slider_float(
            label="Gamma blue",
            id=Widgets.gamma_slider_b,
            min_value=0.001,
            max_value=2,
            callback=lambda sender: Config.gamma_slider_callback(sender, 2),
            default_value=Config.gamma_b,
        )

        dpg.add_color_picker(
            id=Widgets.color_picker,
            default_value=Config.color_picker,
            callback=lambda: Config.color_picker_callback(),
        )

    dpg.set_primary_window(main_window, True)
    dpg.setup_viewport()
    dpg.set_viewport_title(title="Python Night Light")
    dpg.set_viewport_width(WIDTH)
    dpg.set_viewport_height(HEIGHT)
    dpg.start_dearpygui()


if __name__ == "__main__":
    main()
