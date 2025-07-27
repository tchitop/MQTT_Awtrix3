import subprocess
import sys
import platform
import os
import re
import json

def run_pip_install():
    """
    Attempts to install required Python packages using pip.
    Checks if pip is available and handles basic errors.
    """
    required_packages = ["paho-mqtt", "requests"]
    
    print("\n--- Checking and Installing Python Dependencies ---")
    
    # Check if pip is available
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print("Error: pip command not found.")
        print("Please ensure Python and pip are correctly installed and added to your system's PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError:
        print("Error: pip is not working correctly.")
        print("Please check your Python and pip installation.")
        sys.exit(1)

    for package in required_packages:
        print(f"Checking for {package}...")
        try:
            # Try to import to see if it's already installed
            # Special handling for paho-mqtt which is imported as paho.mqtt
            if package == "paho-mqtt":
                import paho.mqtt.client
            else:
                __import__(package.replace('-', '_')) 
            print(f"{package} is already installed.")
        except ImportError:
            print(f"Installing {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"{package} installed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"Error installing {package}: {e}")
                print("Please try running this script with administrator/root privileges if you encounter permission errors.")
                sys.exit(1)
            except Exception as e:
                print(f"An unexpected error occurred during {package} installation: {e}")
                sys.exit(1)
    print("All required Python dependencies are met.")
    print("---------------------------------------------")

def get_os_type():
    """Tries to automatically detect OS, otherwise prompts user."""
    detected_os = platform.system()
    os_type = "Unknown"

    if detected_os == "Darwin":
        os_type = "macOS"
    elif detected_os == "Windows":
        os_type = "Windows"
    elif detected_os == "Linux":
        os_type = "Linux"
    else:
        print(f"\nCould not automatically detect OS (detected: {detected_os}).")
        os_input = input("What OS is this (e.g., macOS, Windows, Linux)?: ").strip().lower()
        if "macos" in os_input or "osx" in os_input:
            os_type = "macOS"
        elif "windows" in os_input:
            os_type = "Windows"
        elif "linux" in os_input:
            os_type = "Linux"
        else:
            print("Invalid OS input. Defaulting to 'Unknown'.")
    return os_type

def get_input(prompt, default=None, validation_regex=None, error_message="Invalid input."):
    """Helper function to get user input with optional default and validation."""
    while True:
        user_input = input(f"{prompt} {'(Default: ' + str(default) + ')' if default is not None else ''}: ").strip()
        if not user_input and default is not None:
            return default
        if validation_regex and not re.fullmatch(validation_regex, user_input):
            print(error_message)
        else:
            return user_input

def get_color_input(prompt, default_color_str="255,255,255"):
    """Helper to get a color input (R,G,B) and return as a list."""
    while True:
        color_str = get_input(prompt, default=default_color_str,
                              validation_regex=r"^\d{1,3},\d{1,3},\d{1,3}$",
                              error_message="Please enter color as R,G,B (e.g., 255,0,0).")
        try:
            r, g, b = map(int, color_str.split(','))
            if all(0 <= c <= 255 for c in [r, g, b]):
                return [r, g, b]
            else:
                print("Color components must be between 0 and 255.")
        except ValueError:
            print("Invalid color format. Please use R,G,B.")

def main_awtrix_builder():
    """
    The main function for the interactive AWTRIX script builder.
    """
    print("--- AWTRIX MQTT Custom Script Builder ---")
    print("This tool will generate a 'mqtt_awtrix_script.py' based on your input.")
    print("-----------------------------------------")

    os_type = get_os_type()
    print(f"\nDetected OS: {os_type}")
    print("-" * 30)

    # Get MQTT Broker details
    mqtt_broker = get_input("Enter MQTT Broker IP/Hostname", default="127.0.0.1")
    mqtt_port = get_input("Enter MQTT Port", default="1883", validation_regex=r"^\d+$", error_message="Port must be a number.")
    mqtt_topic_base = get_input("Enter Base MQTT Topic (e.g., awtrix/custom)", default="awtrix/custom")
    
    # Get Weather URL
    weather_url = get_input("Enter wttr.in weather URL (e.g., https://wttr.in/Frankfurt?format=j1)", default="https://wttr.in/50.0104,9.0294?format=j1")

    custom_messages = []
    message_count = 0

    print("\n--- Custom Messages ---")
    print("You can add multiple custom messages to be displayed on your AWTRIX.")
    print("Type 'done' for the text to finish adding messages.")

    while True:
        message_count += 1
        print(f"\n--- Message {message_count} ---")
        text = get_input(f"Enter text for message {message_count} (or 'done' to finish)", validation_regex=r"^(?!done$).*|done$", error_message="Please enter a text.")
        if text.lower() == "done":
            break
        
        icon = get_input(f"Enter icon ID for message {message_count} (optional, leave empty for no icon)", validation_regex=r"^\d*$|^$", error_message="Icon ID must be a number or empty.")
        color = get_color_input(f"Enter color for message {message_count} (R,G,B)", default_color_str="255,255,255")
        duration = get_input(f"Enter duration in seconds for message {message_count}", default="5", validation_regex=r"^\d+$", error_message="Duration must be a number.")
        
        custom_topic = f"{mqtt_topic_base}/custom_msg_{message_count}"
        
        custom_messages.append({
            "text": text,
            "icon": icon if icon else "None",
            "color": color,
            "duration": duration,
            "topic": custom_topic
        })

    # Corrected Template for the generated AWTRIX script
    # Notice that placeholders like ###MQTT_BROKER### are now *inside* the quotes.
    template_content = """\
import time
import json
import requests
import paho.mqtt.client as mqtt

# Config
on = 1
MQTT_BROKER = "###MQTT_BROKER###"
MQTT_PORT = ###MQTT_PORT###
MQTT_TOPIC = "###MQTT_TOPIC###"

# Optionale Anpassung der Wetter-URL für deinen Standort
WEATHER_URL = "###WEATHER_URL###"

def get_weather():
    data = requests.get(WEATHER_URL).json()
    current = data["current_condition"][0]
    temp = int(current["temp_C"])
    desc_en = current["weatherDesc"][0]["value"]
    print("DEBUG-WetterDesc:", current["weatherDesc"][0]["value"])
    return temp, desc_en


def send_awtrix_message(client, text, icon=None, color=[255, 255, 255], duration=5, topic=MQTT_TOPIC):
    payload = {
        "text": text,
        "duration": duration,
        "color": color
    }
    if icon:
        payload["icon"] = icon
    print(f"Sende an {topic}: {json.dumps(payload)}")
    client.publish(topic, json.dumps(payload))


def main():
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    while True:
        try:
            temp, desc = get_weather()
            # Wetterbeschreibungen übersetzen
            translations = {
                "Partly cloudy": "Teilweise bewölkt",
                "Sunny": "Sonnig",
                "Clear": "Klar",
                "Cloudy": "Bewölkt",
                "Overcast": "Bedeckt",
                "Light rain": "Leichter Regen",
                "Moderate rain": "Mäßiger Regen",
                "Heavy Rain Shower": "Starker Regen",
                "Heavy rain shower, thunderstorm in vicinity": "Starker Regen, Gewitter in der Nähe",
                "Snow": "Schnee",
                "Thunderstorm": "Gewitter",
                "Drizzle": "Nieselregen",
                "Mist": "Nebel",
                "Fog": "Nebel",
                "Haze": "Dunst",
                "Dust": "Staub",
                "Sand": "Sand",
                "Squalls": "Windböen",
                "Tornado": "Tornado",
            }
            translated_desc = translations.get(desc, desc) # Übersetzt, wenn gefunden, sonst original

            # Standard-Wetteranzeige (immer dabei)
            send_awtrix_message(client, f"{translated_desc}", icon="16785", color=[0, 200, 255], duration=5, topic="awtrix/custom/Wetter")
            send_awtrix_message(client, f"{temp}°C", icon="2497", color=[255, 0, 255], duration=5, topic="awtrix/custom/Temp")

            # --- GENERATED CUSTOM MESSAGES ---
###GENERATED_MESSAGES_CALLS###
            # --- END GENERATED CUSTOM MESSAGES ---

            print("-" * 204)
            time.sleep(30)
        except Exception as e:
            print(f"Ein Fehler ist aufgetreten: {e}")
            print("Warte 60 Sekunden und versuche es erneut...")
            time.sleep(60)

if __name__ == "__main__":
    main()
"""

    # Prepare placeholder replacements (values are now directly embedded as strings/numbers)
    replacements = {
        "###MQTT_BROKER###": mqtt_broker, # Removed extra quotes here
        "###MQTT_PORT###": mqtt_port,
        "###MQTT_TOPIC###": f"{mqtt_topic_base}/Wetter", # Removed extra quotes here
        "###WEATHER_URL###": weather_url, # Removed extra quotes here
    }

    generated_message_calls = []

    for i, msg in enumerate(custom_messages):
        icon_arg = f'icon="{msg["icon"]}"' if msg["icon"] != "None" else ''
        
        call_str = (
            f'            send_awtrix_message(client, "{msg["text"]}", '
            f'{icon_arg}{", " if icon_arg else ""}'
            f'color={msg["color"]}, duration={msg["duration"]}, '
            f'topic="{msg["topic"]}")'
        )
        generated_message_calls.append(call_str)

    replacements["###GENERATED_MESSAGES_CALLS###"] = "\n".join(generated_message_calls)


    # Apply replacements to the template
    for placeholder, value in replacements.items():
        template_content = template_content.replace(placeholder, str(value)) # Ensure value is string

    output_filename = "mqtt_awtrix_script.py"
    try:
        with open(output_filename, "w") as f:
            f.write(template_content)

        print(f"\nSuccessfully generated '{output_filename}' in the current directory!")
        print(f"You can now run your personalized script by executing:")
        print(f"    python {output_filename}")
        print("Please review the generated script to ensure all settings are correct.")

    except Exception as e:
        print(f"An error occurred during script generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("--- Starting AWTRIX Script Generator ---")
    run_pip_install() # First, ensure all dependencies are installed
    main_awtrix_builder() # Then, run the interactive builder
    print("\n-----------------------------------------")
    print("Setup and script generation complete!")
    print("-----------------------------------------")