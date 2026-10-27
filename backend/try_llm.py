from app.services.llm_service import get_llm_service

llm = get_llm_service()
result = llm.generate(
    system_prompt="You are a concise assistant. Answer in one sentence.",
    user_prompt="What is a vector database used for?",
)
print(result.text)
print("tokens in/out:", result.input_tokens, "/", result.output_tokens)
