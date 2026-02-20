"""
AI Client Factory — 根據用戶 BYOK 配置建立對應的 AI client
統一介面：generate_json() / chat()
"""

import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

from app.config import settings
from app.schemas.ai_config import AI_PROVIDERS

logger = logging.getLogger(__name__)


@dataclass
class AIConfig:
    """AI 配置資料"""
    provider: str
    model: str
    api_key: str
    is_byok: bool = False


class BaseAIClient:
    """AI Client 基底類別"""

    def __init__(self, config: AIConfig):
        self.config = config

    def generate_json(self, prompt: str, temperature: float = 0.5) -> Optional[Dict]:
        raise NotImplementedError

    def chat(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 4096) -> Optional[str]:
        raise NotImplementedError

    @property
    def provider_label(self) -> str:
        suffix = " (BYOK)" if self.config.is_byok else ""
        return f"{self.config.provider}{suffix}"


class GeminiClient(BaseAIClient):
    """Google Gemini Client"""

    def generate_json(self, prompt: str, temperature: float = 0.5) -> Optional[Dict]:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.config.api_key)
            llm = genai.GenerativeModel(self.config.model)
            response = llm.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    response_mime_type="application/json",
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"GeminiClient.generate_json error: {e}")
            return None

    def chat(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 4096) -> Optional[str]:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.config.api_key)
            llm = genai.GenerativeModel(self.config.model)

            # 轉換 messages 為 Gemini 格式
            history = []
            last_user_msg = ""
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "system":
                    last_user_msg = content + "\n\n"
                    continue
                if role == "user":
                    last_user_msg += content
                else:
                    # 先把之前累積的 user msg 加入
                    if last_user_msg:
                        history.append({"role": "user", "parts": [last_user_msg]})
                        last_user_msg = ""
                    history.append({"role": "model", "parts": [content]})

            chat = llm.start_chat(history=history)
            response = chat.send_message(
                last_user_msg or "Hello",
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            return response.text
        except Exception as e:
            logger.error(f"GeminiClient.chat error: {e}")
            return None


class OpenAIClient(BaseAIClient):
    """OpenAI Client"""

    def _get_client(self):
        from openai import OpenAI
        return OpenAI(api_key=self.config.api_key)

    def generate_json(self, prompt: str, temperature: float = 0.5) -> Optional[Dict]:
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "你是一位專業的股票分析師，必須以 JSON 格式回覆。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"OpenAIClient.generate_json error: {e}")
            return None

    def chat(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 4096) -> Optional[str]:
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAIClient.chat error: {e}")
            return None


class GroqClient(BaseAIClient):
    """Groq Client"""

    def _get_client(self):
        from groq import Groq
        return Groq(api_key=self.config.api_key)

    def generate_json(self, prompt: str, temperature: float = 0.5) -> Optional[Dict]:
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "你是一位專業的股票分析師，必須以 JSON 格式回覆。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"GroqClient.generate_json error: {e}")
            return None

    def chat(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 4096) -> Optional[str]:
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"GroqClient.chat error: {e}")
            return None


_CLIENT_MAP = {
    "gemini": GeminiClient,
    "openai": OpenAIClient,
    "groq": GroqClient,
}


class AIClientFactory:
    """AI 客戶端工廠"""

    @staticmethod
    def resolve_config(user, db=None) -> Optional[AIConfig]:
        """查詢用戶自訂 AI 配置，有則解密回傳，無則回傳 None"""
        if db is None:
            return None
        try:
            from app.models.user_ai_config import UserAIConfig
            from app.services.crypto_service import decrypt_credentials

            record = db.query(UserAIConfig).filter(
                UserAIConfig.user_id == user.id
            ).first()
            if not record:
                return None

            decrypted = decrypt_credentials(record.encrypted_api_key)
            api_key = decrypted.get("api_key", "")
            if not api_key:
                return None

            return AIConfig(
                provider=record.provider,
                model=record.model,
                api_key=api_key,
                is_byok=True,
            )
        except Exception as e:
            logger.warning(f"Failed to resolve user AI config: {e}")
            return None

    @staticmethod
    def create_client(config: AIConfig) -> Optional[BaseAIClient]:
        """根據 config 建立對應的 AI client"""
        cls = _CLIENT_MAP.get(config.provider)
        if cls is None:
            logger.error(f"Unknown AI provider: {config.provider}")
            return None
        return cls(config)

    @staticmethod
    def get_system_config() -> AIConfig:
        """取得系統預設的 AI 配置（Gemini）"""
        return AIConfig(
            provider="gemini",
            model=settings.AI_MODEL_FREE,
            api_key=settings.GOOGLE_API_KEY,
            is_byok=False,
        )

    @staticmethod
    def test_client(provider: str, model: str, api_key: str) -> Dict:
        """測試 API key 是否有效"""
        config = AIConfig(provider=provider, model=model, api_key=api_key, is_byok=True)
        client = AIClientFactory.create_client(config)
        if client is None:
            return {"success": False, "message": f"不支援的 provider: {provider}"}

        result = client.chat(
            messages=[
                {"role": "user", "content": "回覆 OK 即可，不需要其他文字。"}
            ],
            temperature=0,
            max_tokens=10,
        )
        if result is not None:
            return {"success": True, "message": f"{provider}/{model} 連線成功"}
        return {"success": False, "message": f"{provider}/{model} API Key 無效或連線失敗"}
