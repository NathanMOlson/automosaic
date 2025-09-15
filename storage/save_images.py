import os
import pyinotify
import sys


class EventProcessor(pyinotify.ProcessEvent):
    def save_image(self, filename) -> None:
        print(f"Saving {os.path.basename(filename)}")
        # Mark the image as saved by creating an empty file with the same name and ".saved" appended
        with open(filename + ".saved", "w") as f:
            pass

    def process_IN_CLOSE_WRITE(self, event) -> None:
        if event.pathname.split('.')[-1] == "saved":
            return
        self.save_image(event.pathname)


def main() -> None:
    watch_manager = pyinotify.WatchManager()
    event_notifier = pyinotify.Notifier(watch_manager, EventProcessor())

    watch_manager.add_watch(os.path.abspath(sys.argv[1]), pyinotify.IN_CLOSE_WRITE)
    event_notifier.loop()


if __name__ == "__main__":
    main()
