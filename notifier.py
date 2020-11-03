import feedparser
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QWidget, QAction, QMenu
import sys
import os
import json
import time
import webbrowser

# Get path for temp folder when the program is executed
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Thread for opening the web browser
# Only seems to be a problem in Linux
class OpenWeb(QThread):
    def __init__(self, function, *args, **kwargs):
        super(OpenWeb, self).__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        self.function(*self.args, **self.kwargs)

def open_update(url):
    webbrowser.open(url, 2)

def open_hs2():
    webbrowser.open("https://www.homestuck2.com/", 2)

# Thread for checking for HS^2 updates
class Worker(QThread):
    updateSignal = pyqtSignal(bool)

    def __init__(self,  parent=None):
        QThread.__init__(self, parent)
        self.running = False

    @pyqtSlot()
    def run(self):
        self.running = True
        while self.running:
            self.check_for_update()
            time.sleep(30)  # Check for update every 30 seconds

    def stop(self):
        self.running = False
        self.terminate()

    def check_for_update(self):
        url = "https://www.homestuck2.com/story/rss"
        self.data_dict = {}
        feed = feedparser.parse(url)
        self.data_dict["last_update_date"] = feed.feed.updated

        if os.path.isfile(resource_path("data/last_update.json")):  # Check if last_update.json exists
            with open(resource_path("data/last_update.json"), "r") as last_update_file:  # Open it for reading
                local_data = json.loads(last_update_file.read())  # Copy the content of the dict into another dict
                if local_data["last_update_date"] != self.data_dict["last_update_date"]:
                    self.updateSignal.emit(True)  # If the dates of both dicts don't match, send the update signal
                else:
                    print("No new upd8...")
            # Write the relevant update data to the JSON file
            for index, entries in enumerate(feed.entries):
                if entries.updated != self.data_dict["last_update_date"]:
                    self.data_dict["last_update_first_page"] = feed.entries[index - 1].title
                    self.data_dict["last_update_first_page_title"] = feed.entries[index - 1].description
                    self.data_dict["last_update_first_page_url"] = feed.entries[index - 1].link
                    self.data_dict["last_update_page_count"] = index
                    break
            with open(resource_path("data/last_update.json"), "w") as last_update_file:  # Open the JSON for writing
                json.dump(self.data_dict, last_update_file)  # Write the new last update data to the local JSON
        else:
            with open(resource_path("data/last_update.json"), "w") as last_update_file:  # Open the JSON for writing
                json.dump(self.data_dict, last_update_file)  # Write the new last update data to the local JSON


class Notifier(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Creating the system tray icon
        self.tray_icon = QSystemTrayIcon(self)

        # Action for opening the Homestuck^2 website
        open_hs2_action = QAction("Open Homestuck^2", self)
        open_hs2_action.setIcon(QIcon(resource_path('graphics/logo-hs2.ico')))
        open_hs2_action.triggered.connect(self.open_hs2)

        # Action for quiting
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(self.exit)

        # Creating the context menu for the system tray icon and adding the previously defined actions
        tray_menu = QMenu()
        tray_menu.addAction(open_hs2_action)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)  # Adding the context menu to the tray icon

        self.tray_icon.setIcon(QIcon(resource_path('graphics/logo-hs2.ico')))  # Setting the icon
        self.tray_icon.show()

        # Creation of the thread to check for updates
        self.worker = Worker(self)
        self.worker.updateSignal.connect(self.notify_update)
        self.worker.start()

    def notify_update(self):
        update_title = self.worker.data_dict["last_update_first_page_title"]

        # Format the update title
        update_title += "\n(" + str(self.worker.data_dict["last_update_page_count"]) + " pages long.)"

        self.tray_icon.showMessage("Homestuck^2 Update", update_title,
                                   QIcon(resource_path("graphics/logo-hs2.ico")))
        self.tray_icon.messageClicked.connect(self.open_update)  # Open the new update

    # Open the HS^2 website on the first page of the last update
    def open_update(self):
        self.opener = OpenWeb(open_update, self.worker.data_dict["last_update_first_page_url"])
        self.opener.start()
        self.tray_icon.messageClicked.disconnect()

    # Open the Homestuck^2 website
    def open_hs2(self):
        self.opener = OpenWeb(open_hs2)
        self.opener.start()

    def exit(self):
        self.worker.stop()  # Stop the thread to check for updates
        self.close()  # Actually close the window

def main():
    # Create the application
    app = QApplication(sys.argv)
    w = Notifier()

    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())