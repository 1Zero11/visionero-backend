class Executable():
    def __init__(self, path: str, id: int):
        self.path = path
        self.is_running = False
        self.id = id
