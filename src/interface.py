"""User interface handler."""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

import lib
import widget
from database import Database
from config import Config
from action import Action

DEFAULT_WIDTH = 500
DEFAULT_HEIGHT = 400


class Interface:
    """Interface class."""

    # windows variable structure: {"<WINDOW NAME>": "<WIDGET OBJECT>"}
    __windows = {}
    __database = None
    _is_done_btn = None
    _show_all = False

    def __init__(self):
        """Initialize UserInterface class."""
        self.__config = Config()
        self.__action = Action()
        self.__database = Database(self.__config.database_path)

    def start(self):
        """Start user interface by generating widgets and objects."""
        add_new_btn = widget.Button("button_normal", "New")
        is_done_btn = widget.Button("button_light", "0")
        is_done_btn.on_click(self.__action.all_items, *(self, "show"))
        self._is_done_btn = is_done_btn
        c_height, c_width = self.__config.height_and_width
        height = c_height if c_height > 0 else DEFAULT_HEIGHT
        width = c_width if c_width > 0 else DEFAULT_WIDTH
        main_window = widget.Window("Main", "MTodo", None, width, height, {add_new_btn: "left", is_done_btn: "left"}, True)
        main_window.set_icon(self.__config.software_icon_file)
        main_window.on_resize(self.__action.reload_items, *(self, "refresh"))
        main_window.delegate("on_resize", self._update_preferences)
        self.__windows.update({"main_window": main_window})
        add_new_btn.on_click(self.__action.add_item, *(self, "new"))
        self.refresh(main_window)
        self.render()

    def set_show_all_mode(self, mode: bool):
        """Update show_all mode."""
        self._show_all = mode

    def get_show_all_mode(self):
        """Return show_all mode."""
        return self._show_all

    def refresh(self, window, win_width=DEFAULT_WIDTH):
        """Refresh main window widgets and objects."""
        is_done_rows = self.__database.select_items("is_done=1")
        if self._show_all is False:
            active_rows = self.__database.select_items("is_done=0")
        else:
            active_rows = self.__database.select_items()

        if is_done_rows is None or active_rows is None:
            return False

        window.cleanup()

        if len(active_rows) == 0:
            not_item_alert = widget.Alert("alert_normal",
                                          "No Todo Found.",
                                          "Click on 'Add New' button on your top-left side.")
            window.join(not_item_alert)
        else:
            is_done_counter = 0
            for item in active_rows:
                name = "todo_item_normal"
                if item["is_important"] == 1:
                    name = "todo_item_important"
                if item["is_done"] == 1:
                    name = "todo_item_done"

                if item["description"] and len(item["description"]) > int(win_width/10):
                    description = item["description"].replace('\n', '')[:int(win_width/10)] + "....."
                else:
                    description = item["description"].replace('\n', '')

                item_button = widget.BigButton(name, "<big><b>{}</b></big>\n{}".format(item["title"], description))
                item_button.on_click(self.__action.edit_item, *(self, "edit",
                                                                item["todo_id"],
                                                                item["title"],
                                                                item["description"],
                                                                True if item["is_done"] == 1 else False,
                                                                True if item["is_important"] == 1 else False))
                window.join(item_button)

        # update is_done button counter
        self._is_done_btn.set_label(str(len(is_done_rows)))

        self.load_style()
        window.render()

    def todo_item(self, todo_id=None, title=None, description=None, is_done=None, is_important=None):
        """New item window."""
        window_subtitle = "New Item"
        save_btn = widget.Button("button_blue", "Save")
        header_btns = {save_btn: "left"}
        if todo_id is not None:
            del_btn = widget.Button("button_red", "Delete")
            del_btn.on_click(self.__action.del_item, *(self, "del", todo_id))
            header_btns.update({del_btn: "left"})
            window_subtitle = "Edit Item"

        window = widget.Window("Main", "MTodo", window_subtitle, 500, 480, header_btns, False)
        self.__windows["todo_item"] = window
        box = widget.Box("new_data", True)
        switch_box = widget.Box("switch_data", True)

        title_text = widget.Input("title", "Title", False)
        title_text.set_text(title)

        description_text = widget.Input("description", "Description", True)
        description_text.set_text(description)

        is_done_switch = widget.Switch("is_done")
        is_done_switch.set_value(is_done)
        is_done_label = widget.Label("is_done_label", "Is done")
        is_done_box = widget.Box("is_done_data", False)

        is_important_switch = widget.Switch("is_important")
        is_important_switch.set_value(is_important)
        is_important_label = widget.Label("is_important_label", "Is Important")
        is_important_box = widget.Box("is_important_data", False)

        is_done_box.join(is_done_label, True, True)
        is_done_box.join(is_done_switch)

        is_important_box.join(is_important_label, True, True)
        is_important_box.join(is_important_switch)

        box.join(title_text)
        box.join(description_text)
        switch_box.join(is_important_box)
        switch_box.join(is_done_box)

        if todo_id is None:
            save_btn.on_click(self.__action.add_item, *(self, "save",
                                                        title_text,
                                                        description_text,
                                                        is_done_switch,
                                                        is_important_switch))
        else:
            save_btn.on_click(self.__action.edit_item, *(self, "save",
                                                         todo_id,
                                                         title_text,
                                                         description_text,
                                                         is_done_switch,
                                                         is_important_switch))
        window.join(box)
        window.join(switch_box)
        window.render()

    def get_window(self, window_name):
        return self.__windows[window_name]

    def render(self):
        """Run software GUI."""
        Gtk.main()

    def destroy(self, window_name: str):
        """Destroy a window."""
        self.__windows[window_name].destroy()

    def load_style(self):
        """Load CSS theme."""
        style = Gtk.CssProvider()
        style.load_from_path(self.__config.software_style_file)

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style,
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

        if self.__config.software_is_dark_style == "true":
            settings = Gtk.Settings.get_default()
            settings.set_property("gtk-application-prefer-dark-theme", True)

    def _update_preferences(self, event_name: str, related_info: dict) -> None:
        """Update user preferences.

        :param event_name: callback event name
        :type event_name: str
        :param related_info: event related info
        :type related_info: dict

        :return: none
        :rtype: None
        """
        if event_name == "on_resize":
            self.__config.update_file(related_info)
