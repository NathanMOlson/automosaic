import os
import pyinotify
import sys


class EventProcessor(pyinotify.ProcessEvent):
    def save_image(self, filename) -> None:
        print(f"Saving {os.path.basename(filename)}")
        # Mark the image as saved by creating an empty file with the same name and ".saved" appended
        with open(filename + ".saved", "w") as f:
            pass

    def handle_new_file(self, filename: str) -> None:
        if filename.split('.')[-1] != "jxl":
            return
        self.save_image(filename)

    def process_IN_CLOSE_WRITE(self, event) -> None:
        self.handle_new_file(event.pathname)


def main() -> None:
    watch_manager = pyinotify.WatchManager()
    event_processor = EventProcessor()
    event_notifier = pyinotify.Notifier(watch_manager, event_processor)

    image_dir = os.path.abspath(sys.argv[1])
    print(f"Watching {image_dir} for images to move to storage")
    watch_manager.add_watch(image_dir, pyinotify.IN_CLOSE_WRITE)
    
    with os.scandir(image_dir) as entries:
        for entry in entries:
            if entry.is_file():
                event_processor.handle_new_file(entry.path)
    event_notifier.loop()


if __name__ == "__main__":
    main()
