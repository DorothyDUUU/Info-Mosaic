"""Common variables."""


class CommonConfig:
    def __init__(
        self,
    ):
        self.__dict__ = {
            "LOG_CONFIG": {"dir": "./logger/log"},
            # ! add your api key and model settings here
            "SANDBOX": {"tool_link": "http://127.0.0.1:30010"},
            "gpt-4o": {
                "url": "http://123.129.219.111:3000/v1",
                "authorization": "EMPTY",
                "retry_time": 3,
            },
            "debug_mode": False,
        }

    def __getitem__(self, key):
        return self.__dict__.get(key, None)
