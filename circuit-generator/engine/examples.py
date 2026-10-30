EXAMPLES = {
 "street_light": {"name": "Automatic Street Light", "desc": "LDR senses darkness and switches an LED.", "components": ["arduino_uno", "ldr", "led"]},
 "motion_alarm": {"name": "Motion Alarm", "desc": "PIR sensor triggers a buzzer and warning LED.", "components": ["arduino_uno", "pir", "buzzer", "led"]},
 "distance": {"name": "Distance Detector", "desc": "Ultrasonic ranging shown on an OLED with buzzer.", "components": ["arduino_uno", "hc_sr04", "oled", "buzzer"]},
 "temperature": {"name": "Temperature Monitor", "desc": "ESP32 reads a DHT11 and displays it on an OLED.", "components": ["esp32", "dht11", "oled"]},
 "servo": {"name": "Servo Control", "desc": "Potentiometer sets servo angle.", "components": ["arduino_uno", "potentiometer", "servo"]},
}
