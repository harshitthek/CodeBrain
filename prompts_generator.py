from openai import OpenAI
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

client = OpenAI(
    base_url="https://api.deepseek.com/",
    api_key=os.getenv("DEEPSEEK_API_KEY")  # Read API key from environment variable
)

completion = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {
                "role": "system",
                "content": "You are an expert prompt engineer for large language models. Please compose an intelligent assistant prompt based on user requirements to guide LLM content generation. Requirements:\n1. Output in YAML format\n2. Align with user requirements, describing the assistant's positioning, capabilities, and knowledge reserve\n3. The prompt should be clear, precise, and easy to understand, keeping it as concise as possible while maintaining high quality\n4. Output only the prompt without extra conversational explanations"
        },
        {
                "role": "user",
                "content": "Please help me generate a prompt for a 'Test Case Generation Assistant'"
        }
    ]
)

print(completion.choices[0].message.content)