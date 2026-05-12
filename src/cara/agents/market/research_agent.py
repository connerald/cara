from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
import os

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

model = ChatOpenAI(
    model="deepseek-v4-pro",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    extra_body={
        "thinking": {
            "type": "disabled"
        }
    }
)

agent = create_agent(
    model=model,
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user", 
                "content": "What's the weather in Beijing?"
                }
            ]
    }
)

print(result["messages"][-1].content_blocks)