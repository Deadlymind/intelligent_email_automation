import openai
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# set the OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

def generate_response(prompt, max_tokens=150, temperature=0.7):
    try:
        response = openai.Completion.create(
            engine='text-davinci-003',  # or the engine you have access to
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            n=1,
            stop=None,
        )
        message = response.choices[0].text.strip()
        return message
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return None
