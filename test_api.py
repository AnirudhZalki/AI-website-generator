import os, openai

openai.api_key = os.getenv("OPENAI_API_KEY")

resp = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello GPT, say hi in one sentence."}]
)

print(resp.choices[0].message.content)
