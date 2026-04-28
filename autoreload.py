import subprocess
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RestartHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print(f"Изменен: {event.src_path}. Перезапуск бота")
            subprocess.run(['systemctl', 'restart', 'valera_bot'])

if __name__ == "__main__":
    event_handler = RestartHandler()
    observer = Observer()
    observer.schedule(event_handler, path='/opt/valera_bot', recursive=True)
    observer.start()
    print("Отслеживаю изменение файлов")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
