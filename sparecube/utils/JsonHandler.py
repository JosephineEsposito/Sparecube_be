from datetime import datetime, timezone
import json


class JsonHandler:
    @staticmethod
    def create_message(message: str, data: dict) -> json:
        now = datetime.now(timezone.utc).astimezone()
        timestamp = now.isoformat()
        producer = f"Sparecube_Website"

        header = {
            "Producer": producer,
            "Message": message,
            "DateTime": timestamp,
            "Message_Id": f"{producer}:{message}:{timestamp}"
        }

        full_message = header
        full_message["Data"] = data

        if not isinstance(full_message, str):
            full_message = json.dumps(full_message)

        return full_message
