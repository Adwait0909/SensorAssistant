import base64
import io
import json
import re
from typing import Any, Dict
from urllib import error, request

from PIL import Image

from config import Config


class GeminiVisionService:
    """Small REST client for identifying electrical components with Gemini."""

    ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    @classmethod
    def is_available(cls) -> bool:
        return bool(Config.GEMINI_API_KEY)

    @classmethod
    def identify_component(cls, image_bytes: bytes) -> Dict[str, Any]:
        if not cls.is_available():
            return {
                "model_available": False,
                "component": None,
                "confidence": 0.0,
                "category": None,
                "message": "Gemini API key is not configured."
            }

        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.verify()
            image_format = (image.format or "JPEG").lower()
            mime_type = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "webp": "image/webp",
            }.get(image_format)
            if not mime_type:
                raise ValueError("Unsupported image format.")

            prompt = (
                "Identify the single electronics component in this image. "
                "Do not restrict the identification to a fixed component list. "
                "Use the most specific real-world component name you can determine. "
                "The component may be any electrical or electronic part used to build "
                "a circuit, including sensors, switches, buttons, buzzers, LEDs, "
                "resistors, capacitors, motors, modules, boards, and connectors. "
                "If the image is unclear, contains multiple components, or no electrical "
                "or electronic component can be identified, set component to null. "
                "Return JSON only with exactly these fields: component (string or null), "
                "confidence (number from 0 to 1), category (string or null), "
                "is_sensor (boolean), reason (string)."
            )
            body = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64.b64encode(image_bytes).decode("ascii"),
                            }
                        },
                    ]
                }],
                "generationConfig": {
                    "temperature": 0,
                    "maxOutputTokens": 128,
                    "responseMimeType": "application/json",
                },
            }
            url = cls.ENDPOINT.format(model=Config.GEMINI_MODEL)
            api_request = request.Request(
                url,
                data=json.dumps(body).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": Config.GEMINI_API_KEY,
                },
                method="POST",
            )
            with request.urlopen(api_request, timeout=30) as response:
                response_data = json.loads(response.read().decode("utf-8"))

            text = response_data["candidates"][0]["content"]["parts"][0]["text"]
            result = cls._parse_json(text)
            component = cls._canonical_component(result.get("component"))
            confidence = float(result.get("confidence", 0.0))
            is_sensor = result.get("is_sensor") is True
            if component is None:
                confidence = 0.0
            confidence = round(max(0.0, min(1.0, confidence)) * 100, 1)
            return {
                "model_available": True,
                "component": component,
                "confidence": confidence,
                "category": result.get("category") if component else None,
                "is_sensor": is_sensor,
                "reason": result.get("reason", ""),
                "message": (
                    f"Gemini identified {component} with {confidence}% confidence."
                    if component else
                    "The uploaded image could not be identified."
                ),
            }
        except (ValueError, KeyError, TypeError, IndexError, json.JSONDecodeError) as exc:
            return cls._failure(f"Gemini response could not be understood: {exc}")
        except error.HTTPError as exc:
            try:
                details = json.loads(exc.read().decode("utf-8")).get("error", {}).get("message", "")
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                details = ""
            message = f"Gemini API request failed with HTTP {exc.code}."
            if details:
                message += f" {details}"
            return cls._failure(message)
        except error.URLError:
            return cls._failure("Gemini API could not be reached. Check your internet connection.")
        except TimeoutError:
            return cls._failure("Gemini API request timed out.")

    @staticmethod
    def _parse_json(text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
        if fenced:
            cleaned = fenced.group(1)
        result = json.loads(cleaned)
        if not isinstance(result, dict):
            raise ValueError("Gemini returned a non-object JSON response.")
        return result

    @staticmethod
    def _failure(message: str) -> Dict[str, Any]:
        return {
            "model_available": True,
            "component": None,
            "confidence": 0.0,
            "category": None,
            "is_sensor": False,
            "message": message,
        }

    @staticmethod
    def _canonical_component(value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        key = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
        aliases = {
            "arduino": "Arduino Uno",
            "arduino uno r3": "Arduino Uno",
            "esp 32": "ESP32",
            "raspberry pi 4": "Raspberry Pi",
            "hc sr04": "Ultrasonic Sensor",
            "hc sr04 ultrasonic sensor": "Ultrasonic Sensor",
            "ultrasonic": "Ultrasonic Sensor",
            "hc sr501": "PIR Sensor",
            "pir": "PIR Sensor",
            "photoresistor": "LDR",
            "photocell": "LDR",
            "light dependent resistor": "LDR",
            "sg90": "Servo Motor",
            "servo": "Servo Motor",
            "bo motor": "DC Motor",
            "mq2": "MQ-2 Gas Sensor",
            "mq 2": "MQ-2 Gas Sensor",
            "dht11": "DHT11 Sensor",
            "dht 11": "DHT11 Sensor",
            "lcd": "LCD 16x2",
            "lcd 1602": "LCD 16x2",
            "i2c lcd": "LCD 16x2",
            "button": "Push Button",
            "push button": "Push Button",
            "tactile button": "Push Button",
            "tactile push button": "Push Button",
            "tactile switch": "Push Button",
        }
        return aliases.get(key, value.strip() or None)
