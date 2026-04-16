# Import necessary libraries
import requests
import datetime
import os
import time
import schedule
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

# ===================================================================
# --- CONFIGURATION: LOADED FROM .ENV FILE ---
# ===================================================================
# 1. Your farm's coordinates
LATITUDE = os.getenv("LATITUDE")
LONGITUDE = os.getenv("LONGITUDE")

# 2. Your API Keys are loaded securely from your .env file
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
# ===================================================================


def send_telegram_message(message_text):
    """This function takes a message string and sends it to your Telegram bot."""
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text,
        "parse_mode": "Markdown"
    }
    
    try:
        requests.post(url, json=payload)
        print(f"✅ Telegram message sent successfully at {datetime.datetime.now().strftime('%H:%M:%S')}!")
    except Exception as e:
        print(f"❌ An error occurred while sending Telegram message: {e}")


def check_weather_and_alert():
    """Gets weather data from the free weatherAPI and sends the alert."""
    
    print(f"\nRunning weather check at {datetime.datetime.now().strftime('%H:%M:%S')}...")
    
    # Using the free-tier "5 Day / 3-Hour Forecast" endpoint
    weather_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LATITUDE}&lon={LONGITUDE}&appid={OPENWEATHER_API_KEY}&units=metric"
    
    try:
        weather_data = requests.get(weather_url).json()
        
        # --- NEW LOGIC TO PROCESS 3-HOUR DATA ---
        forecast_list = weather_data['list']
        
        todays_max_temp = -1000 # Start with a very low number
        todays_total_rain_mm = 0
        
        # Loop through the next 8 blocks of 3 hours (24 hours total)
        for forecast_block in forecast_list[:8]:
            # Find the highest temperature in the next 24 hours
            if forecast_block['main']['temp_max'] > todays_max_temp:
                todays_max_temp = forecast_block['main']['temp_max']
            
            # Add up the total rain (if any is forecasted for the 3-hour block)
            if 'rain' in forecast_block and '3h' in forecast_block['rain']:
                todays_total_rain_mm += forecast_block['rain']['3h']
        # --- END OF NEW LOGIC ---

        # Modify the message title based on the time of day
        current_hour = datetime.datetime.now().hour
        if 5 <= current_hour < 12:
            check_type = "Morning Check"
        elif 12 <= current_hour < 17:
            check_type = "Afternoon Update"
        else:
            check_type = "Evening Outlook"
            
        message = f"💧 *Farm Alert: {check_type}* 💧\n\n"
        message += f"Max Temperature (24h): *{todays_max_temp:.2f}°C*\n"
        message += f"Total Forecasted Rain (24h): *{todays_total_rain_mm:.2f} mm*\n\n"

        if todays_total_rain_mm < 5 and todays_max_temp > 30:
            decision = "✅ *Recommendation: Irrigation Needed.* High temperatures and low rain are expected."
        else:
            decision = "❌ *Recommendation: No Irrigation Needed.* Sufficient rain or cooler weather expected."
        
        message += decision
        send_telegram_message(message)

    except KeyError:
        error_message = f"❌ Could not get weather data. The API response was not in the expected format. Please double-check your API key in the .env file."
        print(error_message)
        print("API Response Received:", weather_data)
        send_telegram_message(error_message)
    except Exception as e:
        error_message = f"An unknown error occurred. Error: {e}"
        print(error_message)
        send_telegram_message(error_message)


# ===================================================================
# --- MAIN EXECUTION AND SCHEDULING ---
# ===================================================================
if __name__ == "__main__":
    print("🚀 AI Agent started! The script will now run continuously.")

    # --- Run an immediate test on startup ---
    print("--- Running an immediate test before scheduling... ---")
    check_weather_and_alert() 
    # -------------------------------------------

    print("\nWeather checks are now scheduled for 07:00, 13:00, and 19:00 daily.")
    print("Press Ctrl+C to stop the agent.")

    # Schedule the job to run at specific times every day
    schedule.every().day.at("07:00").do(check_weather_and_alert)
    schedule.every().day.at("13:00").do(check_weather_and_alert)
    schedule.every().day.at("19:00").do(check_weather_and_alert)

    # This loop keeps the script running forever so it can check the schedule
    while True:
        schedule.run_pending()
        time.sleep(1)

# ===================================================================
# --- END OF SCRIPT ---
# ===================================================================