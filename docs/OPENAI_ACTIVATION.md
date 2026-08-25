# OpenAI activation gate

The application is deliberately complete with a deterministic `rules` baseline before paid LLM activation.

Before turning OpenAI on:

1. Choose a currently supported API model from the official OpenAI API documentation.
2. Put the API key in a secret store / `.env`, never GitHub.
3. Set `AI_PROVIDER=openai`.
4. Keep `AI_FALLBACK_TO_RULES=true` initially.
5. Run the regression evaluation and a larger held-out ambiguous dataset.
6. Compare intent accuracy, extraction accuracy, human correction rate, draft edit rate, latency, and cost.

Do not treat model-reported confidence as calibrated probability without measurement.
