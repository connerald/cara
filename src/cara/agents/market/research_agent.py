from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
import os

from dotenv import load_dotenv


def get_weather(city: str) -> str:
    """获取指定城市的天气。"""
    return f"{city} 总是阳光明媚！"


def build_demo_agent():
    load_dotenv(override=True)
    model = ChatOpenAI(
        model=os.getenv("CARA_MODEL", "deepseek-v4-pro"),
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("CARA_MODEL_BASE_URL", "https://api.deepseek.com"),
        extra_body={"thinking": {"type": "disabled"}},
    )
    return create_agent(
        model=model,
        tools=[get_weather],
        system_prompt="你是一个乐于助人的助手。",
    )


if __name__ == "__main__":
    agent = build_demo_agent()
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "北京的天气怎么样？",
                }
            ]
        }
    )
    print(result["messages"][-1].content_blocks)
