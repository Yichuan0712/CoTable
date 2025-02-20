from typing import Optional, List, Dict, Callable
from extractor.request_openai import (
    request_to_chatgpt_35,
    request_to_chatgpt_40,
    request_to_chatgpt_4o,
)
from extractor.request_geminiai import (
    request_to_gemini_15_pro,
    request_to_gemini_15_flash,
)
from dotenv import load_dotenv

load_dotenv()

prompt_list = [
    {"role": "user", "content": "Hello! "},
    {"role": "user", "content": "How are you?"},
]
question = "Please use one word to answer my question."
request_llm: Optional[Callable[[List[Dict[str,str],str],str]]] = None
request_llm = request_to_chatgpt_4o
# request_llm = request_to_gemini_15_pro
res, content, usage, truncated = request_llm(prompt_list, question)
