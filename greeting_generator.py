import datetime
import requests
import random

class GreetingGenerator:
    def __init__(self, speak):
        self.speak = speak

    def generate_greeting(self, context=None):
        try:
            now = datetime.datetime.now()
            hour = now.hour
            if not context:
                if 5 <= hour < 14:
                    return "Good morning! Today your shirt matches the color of your eyes very well."
                elif 14 <= hour < 18:
                    return "Good afternoon! How's your day going?"
                else:
                    return "Good evening! Hope you had a wonderful day."
            response = requests.post(
                'http://192.168.68.54/ai/analyze',
                json={
                    'text': context,
                    'modelName': 'greetings'
                },
                timeout=3
            )
            if response.status_code == 200:
                result = response.json()
                sentiment = result['sentiment']
                if sentiment in ['greeting', 'morning_greeting', 'afternoon_greeting', 'evening_greeting']:
                    return random.choice([
                        "Nice to see you again!",
                        "Hello there! How can I assist you today?",
                        "Great to have you back!"
                    ])
                elif sentiment == 'farewell':
                    return "Good to see you again so soon!"
                elif sentiment == 'gratitude':
                    return "You're welcome! How can I help you today?"
                elif sentiment == 'sympathy':
                    return "I'm here for you. How can I assist?"
                elif sentiment == 'congratulation':
                    return "Congratulations again! How can I help you today?"
                elif sentiment == 'wake_up':
                    return "I'm awake and ready to assist!"
                elif sentiment == 'checking_presence':
                    return "Yes, I'm here and listening!"
                else:
                    if 5 <= hour < 12:
                        return "Good morning! How can I help?"
                    elif 12 <= hour < 18:
                        return "Good afternoon! What can I do for you?"
                    else:
                        return "Good evening! How may I assist you?"
            else:
                print(f"AI analysis failed: {response.text}")
        except Exception as e:
            print(f"Error generating greeting: {str(e)}")
        return "Hello! How can I assist you today?"