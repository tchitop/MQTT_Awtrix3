import time
import json
import requests
import paho.mqtt.client as mqtt

#I know this isnt the best script 
"""TO DO"""
# Fix everything!


#Config 
on = 1
MQTT_BROKER = "127.0.0.1"  # Change if mqtt broker is not on localhost
MQTT_PORT = 1883 # Change if mqtt broker is not on default port
MQTT_TOPIC = "awtrix/custom/Wetter"  # Change if you want to use a different topic

# Optionale Anpassung der Wetter-URL für deinen Standort
WEATHER_URL = "https://wttr.in/50.0104,9.0294?format=j1" # Frankfurt am Main


def set_inactive():
    on = 0
    print("Set banner to inactive.")
    time.sleep(1)  # Short delay
    print("Script will prompt banner after restart or if you set 'on' to 1.")
    time.sleep(1)  # Short delay
    get_weather()  # Call to ensure the script runs at least once
    
def get_weather():
    data = requests.get(WEATHER_URL).json()
    current = data["current_condition"][0]
    temp = int(current["temp_C"])
    desc_en = current["weatherDesc"][0]["value"]

    print("[DEBUG]", current["weatherDesc"][0]["value"])
    return temp, desc_en


def send_awtrix_message(client, text, icon=None, color=[255, 255, 255], duration=5, topic=MQTT_TOPIC):
    payload = {
        "text": text,
        "duration": duration,
        "color": color
    }
    if icon:
        payload["icon"] = icon
    # Debug-Ausgabe des gesendeten Payloads
    print(f"Sende an {topic}: {json.dumps(payload)}")
    client.publish(topic, json.dumps(payload))


def main():
    if on == 1:
        print("!" * 204) # Optimized for MacOS Terminal in Fullscreen
        print("-" * 204) # Optimized for MacOS Terminal in Fullscreen
        print("""
        Script made by UNIX for Seezeit
        Visit: https://xtchitopx.de
        You can find my Github on my website
        If you have any questions, feel free to contact me
        read the README.md for more information
    """)
        print("-" * 204) # Optimized for MacOS Terminal in Fullscreen
        print("!" * 204) # Optimized for MacOS Terminal in Fullscreen
    set_inactive()
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    while True:
        try:
            temp, desc = get_weather()
            if desc == "Partly cloudy":
                desc = "Teilweise bewölkt"
            elif desc == "Sunny":
                desc = "Sonnig"
            elif desc == "Clear":
                desc = "Klar"
            elif desc == "Cloudy":
                desc = "Bewölkt"
            elif desc == "Overcast":            
                desc = "Bedeckt"
            elif desc == "Light rain":
                desc = "Leichter Regen"
            elif desc == "Moderate rain":
                desc = "Mäßiger Regen"
            elif desc == "Heavy Rain Shower":
                desc = "Starker Regen"
            elif desc == "Heavy rain shower, thunderstorm in vicinity":
                desc = "Starker Regen, Gewitter in der Nähe"
            elif desc == "Snow":
                desc = "Schnee"
            elif desc == "Thunderstorm":
                desc = "Gewitter"
            elif desc == "Drizzle": 
                desc = "Nieselregen"
            elif desc == "Mist":
                desc = "Nebel"
            elif desc == "Fog":
                desc = "Nebel"
            elif desc == "Haze":
                desc = "Dunst"
            elif desc == "Dust":
                desc = "Staub"
            elif desc == "Sand":
                desc = "Sand"
            elif desc == "Squalls":
                desc = "Windböen"
            elif desc == "Tornado":
                desc = "Tornado"
            # Erste Nachricht: Wetterzustand
            send_awtrix_message(client, f"{desc}", icon="16785", color=[0, 200, 255], duration=5, topic="awtrix/custom/Wetter")

            send_awtrix_message(client,f"xtchitopx.de", icon="1036", color=[0, 255, 0], duration=5, topic="awtrix/custom/xtchitopx.de_ad_1")

            send_awtrix_message(client, f"{temp}°C", icon="2497", color=[255, 0, 255], duration=5, topic="awtrix/custom/Temp")

            send_awtrix_message(client,f"xtchitopx.de", icon="1036", color=[0, 255, 0], duration=5, topic="awtrix/custom/xtchitopx.de_ad_2")

            send_awtrix_message(client,f"Made for Seezeit by UNIX", icon="500", color=[255, 255, 255], duration=5, topic="awtrix/custom/Seezeit_made_by_unix")
            
            # Ausgabe der Trennlinie direkt nach den letzten Sendungen
            print("-" * 204) # Optimized for MacOS Terminal in Fullscreen
            
            time.sleep(30) # Pause 30 seconds before the next update
        except Exception as e:
            print(f"Ein Fehler ist aufgetreten: {e}")
            print("Warte 60 Sekunden und versuche es erneut...")
            time.sleep(60) # Warte bei Fehlern länger, um nicht zu spammen

if __name__ == "__main__":
    main()