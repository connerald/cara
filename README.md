# cara
cara agent

## 项目结构
cara/
└── src/
    └── cara/
        ├── agents/
        │   ├── market/
        │   │   └── market_agent.py
        │   └── research/
        │       └── research_agent.py
        ├── prompts/
        │   └── router.yaml
        ├── providers/
        │   ├── market/
        │   │   └── base.py
        │   │   └── sina_finance_provider.py
        │   └── news/
        └── tools/
            ├── market/
            │   └── get_stock_price.py
            │   └── get_kline.py
            └── news/
