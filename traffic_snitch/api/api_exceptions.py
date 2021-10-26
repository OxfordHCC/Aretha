class ArethaAPIException(Exception):
    default_message = "There was an error processsing this request"
    def __init__(self, message=default_message, status=400, internal=None):
        if internal is not None:
            print("ArethaAPIException", exc_info=internal)
        self.message = message # human friendly message
        self.status = status
