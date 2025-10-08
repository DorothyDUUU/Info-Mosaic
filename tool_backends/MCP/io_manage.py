from io import StringIO

class OutputCapture:
    def __init__(self):
        self.stdout = StringIO()  # catch std out
        self.stderr = StringIO()  # catch std err

    def write(self, data: str):
        self.stdout.write(data)

    def flush(self):
        self.stdout.flush()
        self.stderr.flush()

    def get_stdout(self) -> str:
        return self.stdout.getvalue()

    def get_stderr(self) -> str:
        return self.stderr.getvalue()

    def close(self):
        self.stdout.close()
        self.stderr.close()

# thread-safe output manager
class ThreadOutputManager:
    def get_capture(self) -> OutputCapture:
        return OutputCapture() 