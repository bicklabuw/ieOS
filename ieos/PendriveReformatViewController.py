from gui.ui_core.ViewController import ViewController
from gui.ui_kit.Label import CenteredXLabel
from gui.ui_kit.Button import Button
# from gui.ui_kit.KeyHintView import KeyHintView
from gui.ui_kit.AlertViewController import AlertViewController

import gui.utils.usb.USBDriveFinder as USBDriveFinder
from gui.utils.usb.USBDriveFinder import USBDriveType
import ieos.FormatIEDrives as FormatIEDrives
from gui.ui_kit.TitleViewController import TitleViewController

import threading
import time

import gui.core.Main as Main


class PendriveReformatViewController(ViewController):
    """
    Controller for the Pendrive Reformat View.
    This controller manages the view and its interactions.
    """

    EXTRA_SPACE_BETWEEN_TITLE_AND_BUTTONS = 0
    EXTRA_SPACE_BETWEEN_TITLES = 4

    def __init__(self):
        super().__init__()
        
        self._main_title = CenteredXLabel(0, text="Pendrive Reformater")
        self.view.add_subview(self._main_title)
        self._title = CenteredXLabel(0, text="No Pendrives Found")
        self.view.add_subview(self._title)

        print("PendriveReformatViewController initialized")

        self.pendrives = {}
        self.buttons = {}

        self.check_for_pendrives = True
        
    def on_appear(self):
        super().on_appear()
        self.check_for_pendrives = True
        threading.Thread(target=self._continuously_check_for_pendrives, daemon=True).start()

    def on_disappear(self):
        """
        Stop checking for pendrives when the view disappears.
        This method is called when the view is no longer active.
        """
        super().on_disappear()
        self.check_for_pendrives = False

    def find_differences_in_pendrives_found(self, old_pendrives, new_pendrives):
        """
        Find differences in the pendrives found.
        This method is called when the view appears to update the list of pendrives.
        """
        old_set = set(old_pendrives)
        new_set = set(new_pendrives)

        added = new_set - old_set
        removed = old_set - new_set
        same = old_set & new_set

        if added:
            print(f"Added pendrives: {added}")
        if removed:
            print(f"Removed pendrives: {removed}")

        return added, removed, same
    
    def _continuously_check_for_pendrives(self):
        """
        Continuously check for pendrives connected to the system.
        This method runs in a separate thread to avoid blocking the main thread.
        """
        while self.check_for_pendrives:
            print("Checking for pendrives...")
            self._find_pendrives()
            time.sleep(3)

    def _get_labels_for_drive(self, drive):
        """
        Get the label for a given drive.
        This method is used to retrieve the label of a pendrive.
        """
        print(f"Getting labels for drive: {drive}")
        drive_labels = []
        if drive["type"] != USBDriveType.DISK:
            TypeError("Drive type must be USBDriveType.DISK")

        for partition in drive["partitions"]:
            label = partition.get("label", None)
            if label:
                drive_labels.append(label)

        if len(drive_labels) == 0:
            drive_labels.append("NO NAME")
        
        return drive_labels

    def _find_pendrives(self):
        """
        Find all pendrives connected to the system.
        If no pendrives are found, update the title.
        If pendrives are found, create buttons for each and add them to the view.
        """
        print("Finding pendrives...")
        pendrives = USBDriveFinder.find_usb_drives()

        num_pendrives = len(pendrives)
        
        if num_pendrives == 0:
            self._title.text = "No Pendrives Found"
        else:
            self._title.text = f"{num_pendrives} Pendrive{'s' if num_pendrives > 1 else ''} Found"
        
        added, removed, same = self.find_differences_in_pendrives_found(self.pendrives, pendrives)

        if added:
            for pendrive in added:
                button = Button(
                    x=0, y=0,
                    width=0, height=0,
                    text=f"{', '.join(self._get_labels_for_drive(pendrives[pendrive]))}",
                    callback=lambda pd=pendrives[pendrive]: self.warn_formatting_pendrive(pd)
                )
                button.set_size_from_text()
                self.view.add_subview(button)
                self.buttons[pendrive] = button
        if removed:
            for pendrive in removed:
                if pendrive in self.buttons:
                    button = self.buttons[pendrive]
                    self.view.remove_subview(button)
                    del self.buttons[pendrive]
                else:
                    print(f"Warning: Pendrive {pendrive} not found in buttons, cannot remove.")
        if same:
            for pendrive in same:
                if pendrive in self.buttons:
                    button = self.buttons[pendrive]
                    button.text = f"{', '.join(self._get_labels_for_drive(pendrives[pendrive]))}"
                    button.set_size_from_text()
                else:
                    print(f"Warning: Pendrive {pendrive} not found in buttons, cannot update.")

        self.pendrives = pendrives

    def warn_formatting_pendrive(self, pendrive):
        """
        Show a warning alert before formatting the pendrive.
        """
        labels = ', '.join(self._get_labels_for_drive(pendrive))
        alert = AlertViewController(
            alert_message=f"Formating {labels} will delete all data. Continue?"
        )

        format_title = TitleViewController(f"Formating {labels}")
        
        def on_yes():
            self.push_view_controller(format_title)
            success = FormatIEDrives.format_usb_drives([pendrive])
            if not success:
                new_alert = AlertViewController(
                    alert_message=f"Failed to format. Reboot & try again. If it fails again, contact Alex."
                )
                new_alert.add_option("OK", lambda: new_alert.pop_view_controller())
                format_title.pop_view_controller()
                print("Reformatting here failed.")
                self.push_view_controller(new_alert)
                alert.pop_after_callback = False
            else:
                format_title.set_title("Formatting Completed!")
                time.sleep(2)
                format_title.pop_view_controller()
        
        alert.add_option("Cancel")
        alert.add_option("Format", on_yes)
        self.push_view_controller(alert)

    def on_layout(self):
        total_height = 0

        _, main_height = self._main_title.get_text_size()

        total_height += main_height + self.EXTRA_SPACE_BETWEEN_TITLES

        _, title_height = self._title.get_text_size()

        total_height += title_height + self.EXTRA_SPACE_BETWEEN_TITLE_AND_BUTTONS

        for button in self.buttons.values():
            button.set_size_from_text()

            button.x = (self.view.width - button.width) / 2

            total_height += button.height

        spacing = (self.view.height - total_height) / (len(self.buttons) + 2)
        current_y = spacing / 2

        self._main_title.y = current_y

        current_y += main_height + self.EXTRA_SPACE_BETWEEN_TITLES

        self._title.y = current_y

        current_y += title_height + self.EXTRA_SPACE_BETWEEN_TITLE_AND_BUTTONS

        for button in self.buttons.values():
            button.y = current_y + (button.height / 2)
            current_y += button.height + spacing

if __name__ == "__main__":
    Main.main(PendriveReformatViewController())
