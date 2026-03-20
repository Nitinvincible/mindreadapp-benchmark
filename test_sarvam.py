import sys
import sarvamai

api_key = sys.argv[1]
client = sarvamai.SarvamAI(api_subscription_key=api_key)

try:
    response = client.chat.completions(
        model="sarvam-30b",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2? Answer in one word."}
        ],
        temperature=0.1,
        top_p=1,
        max_tokens=64,
    )
    import json
    with open("test_out.json", "w") as f:
        f.write(json.dumps(response.model_dump() if hasattr(response, 'model_dump') else vars(response), indent=2))
        
    if hasattr(response, 'choices') and response.choices:
        print("CONTENT:", response.choices[0].message.content)
except Exception as e:
    print("ERROR:", e)
