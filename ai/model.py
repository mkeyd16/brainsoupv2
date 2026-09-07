import os
import logging

# Ensure AVX-512 is disabled in GGML/llama.cpp environment to prevent
# 0xc000001d (illegal instruction) crashes on CPUs with disabled AVX-512 (e.g. Intel Core 3 N355 / E-cores)
os.environ["GGML_AVX512"] = "0"
os.environ["LLAMA_AVX512"] = "0"

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

import config

logger = logging.getLogger("wrld.ai.model")

class ModelManager:
    _instance = None

    def __init__(self):
        self.llm = None
        self.is_loaded = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ModelManager()
        return cls._instance

    def load_model(self, model_path: str = None) -> bool:
        if self.is_loaded and self.llm is not None:
            return True

        path = model_path or str(config.MODEL_PATH)
        if not os.path.exists(path):
            logger.error(f"Model file not found at {path}")
            return False

        if Llama is None:
            logger.error("llama-cpp-python package is not installed.")
            return False

        try:
            logger.info(f"Loading shared model from {path} (n_ctx={config.N_CTX}, n_threads={config.N_THREADS})...")
            self.llm = Llama(
                model_path=path,
                n_ctx=config.N_CTX,
                n_threads=config.N_THREADS,
                n_batch=config.N_BATCH,
                n_gpu_layers=0,  # Strict CPU inference to prevent unsupported GPU driver / ISA crashes
                verbose=False
            )
            self.is_loaded = True
            logger.info("Model successfully loaded into memory.")
            return True
        except Exception as e:
            logger.error(f"Failed to load model from {path}: {e}", exc_info=True)
            self.is_loaded = False
            return False

    def generate(self, system_prompt: str, messages: list[dict], max_tokens: int = config.DEFAULT_MAX_TOKENS) -> str:
        if not self.is_loaded or self.llm is None:
            logger.warning("Attempted generation without loaded model. Mocking or returning fallback.")
            return ""

        formatted_messages = [{"role": "system", "content": system_prompt}] + messages

        try:
            response = self.llm.create_chat_completion(
                messages=formatted_messages,
                max_tokens=max_tokens,
                temperature=config.TEMPERATURE,
                top_p=config.TOP_P,
            )
            content = response["choices"][0]["message"]["content"]
            return content.strip() if content else ""
        except Exception as e:
            logger.error(f"Error during LLM chat completion: {e}")
            return ""
