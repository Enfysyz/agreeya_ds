import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
# Change this line:
from src.rag_engine import ingest_documents

class DocumentChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            print(f"File modified: {event.src_path}. Re-indexing...")
            ingest_documents()

    def on_created(self, event):
        if not event.is_directory:
            print(f"File created: {event.src_path}. Re-indexing...")
            ingest_documents()

def start_watcher():
    event_handler = DocumentChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path='./docs', recursive=True)
    observer.start()
    print("Document watcher started on ./docs...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()