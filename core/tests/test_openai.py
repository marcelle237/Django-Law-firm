# import openai

# openai.api_key = "YOUR_API_KEY" add this on your local testing before uncommenting the following lines

# response = openai.ChatCompletion.create(
#     model="gpt-4.1-mini",
#     messages=[{"role": "user", "content": "Hello!"}]
# )

# print(response.choices[0].message['content'])
# print("Response from OpenAI:", response.choices[0].message['content'])

# test_openai.py
import openai

openai.api_key = "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"

response = openai.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)