# import openai

# openai.api_key = "YOUR_API_KEY"

# response = openai.ChatCompletion.create(
#     model="gpt-4.1-mini",
#     messages=[{"role": "user", "content": "Hello!"}]
# )

# print(response.choices[0].message['content'])
# print("Response from OpenAI:", response.choices[0].message['content'])

# test_openai.py
import openai

have to uncommment this following local testing

response = openai.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)