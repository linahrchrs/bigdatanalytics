from openai import OpenAI
from dotenv import load_dotenv
import os
import sys

# Add project root (optional)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ ERROR: OPENAI_API_KEY not found in environment variables!")
    sys.exit(1)

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# 🧠 System prompt — defines the chatbot's identity and behavior
conversation = [
    {
        "role": "system",
        "content": (
            "You are a helpful and knowledgeable AI assistant working for a university health center. "
            "You provide clear, evidence-based information about health, wellness, and medication. "
            "You are not a doctor, but you help guide users to understand symptoms, medication usage, "
            "and when to seek professional medical attention. Keep your answers friendly, concise, and responsible."
        )
    }
]

print("💬 Health Assistant Chatbot ready! Type 'quit' to exit.\n")

# Chat loop
while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break

    conversation.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation
    )

    reply = response.choices[0].message.content
    print("HealthBot:", reply)
    conversation.append({"role": "assistant", "content": reply})
