import base64
import openai
import os

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Example image path
image_path = "jd_com_historical_cash_flow.png"
base64_image = encode_image(image_path)

# Construct the prompt
prompt = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "Describe this image:"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            }
        ]
    }
]

# Make the API call
response = openai.chat.completions.create(
    model="gpt-4-visual-preview",
    messages=prompt
)

# Print the response
print(response.choices[0].message.content)
