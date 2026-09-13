"""
🔌 MULTI-PROVIDER LLM ADAPTER (Google Gemini, OpenAI & Offline Mock)
Hỗ trợ Native Tool Calling và chuyển đổi linh hoạt qua biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import re
from typing import Dict, Any, List
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider hỗ trợ Native Tool Calling"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    """Offline Mock Provider dùng để chạy thử mà không tốn API Key"""
    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return f"[Mock Chatbot Response]: Xin chào! Tôi đã nhận được câu hỏi '{prompt}'. (Chế độ Chatbot không có Tool tra cứu dữ liệu thời gian thực)."

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        """
        Mô phỏng nhận diện intent gọi Tool. Hỗ trợ vòng lặp ReAct ĐA BƯỚC (Multi-step):
        `prompt` có thể chứa một [SCRATCHPAD] tích lũy các Action/Observation của các
        bước trước (do 'src/app.py' nạp lại), nhờ đó Mock có thể quyết định gọi tiếp
        Tool khác hay đã đủ dữ liệu để trả lời trực tiếp.
        """
        prompt_lower = prompt.lower()

        already_called_academic = "action=academic_query" in prompt_lower
        already_called_schedule = "action=schedule_appointment" in prompt_lower
        already_called_exam = "action=exam_schedule_query" in prompt_lower
        has_prior_observation = "[scratchpad]" in prompt_lower

        # Chỉ dò từ khóa Ý định (intent keywords) trong CÂU HỎI GỐC của người dùng,
        # KHÔNG dò trong nội dung Scratchpad (Thought/Observation của các bước trước),
        # để tránh nhận diện nhầm khi các câu Thought trước đó tình cờ chứa từ khóa
        # như "tra cứu" bên trong phần diễn giải.
        intent_lower = prompt_lower.split("[scratchpad]")[0]

        # Trích mã sinh viên từ câu hỏi (ví dụ SV2026001, SV9999999...)
        sid_match = re.search(r"sv\d{6,}", prompt_lower)
        student_id = sid_match.group(0).upper() if sid_match else "SV2026001"

        # Trích tên Cố vấn nếu đã được tra ra ở Observation của bước trước
        advisor_match = re.search(r"[\"']?advisor[\"']?\s*:\s*[\"']([^\"']+)[\"']", prompt)
        advisor_name = advisor_match.group(1) if advisor_match else "PGS.TS Nguyễn Văn A"

        # Trích thời gian hẹn dạng 'HH:MM DD/MM/YYYY' nếu người dùng có nêu rõ
        dt_match = re.search(r"\d{1,2}:\d{2}\s+(?:ngày\s+)?\d{1,2}/\d{1,2}/\d{4}", prompt)
        datetime_str = dt_match.group(0).replace("ngày ", "") if dt_match else "14:00 15/09/2026"

        # 1) Ý định tra cứu LỊCH THI
        if ("lịch thi" in intent_lower or "lich thi" in intent_lower) and not already_called_exam:
            course_match = re.search(r"\b([A-Z]{2,4}\d{2,4})\b", prompt)
            args = {"student_id": student_id}
            if course_match:
                args["course_code"] = course_match.group(1)
            return {
                "type": "tool_call",
                "tool_name": "exam_schedule_query",
                "arguments": args,
                "thought": f"Người dùng cần tra cứu lịch thi. Tôi sẽ gọi tool exam_schedule_query cho mã {student_id}."
            }

        # 2) Ý định ĐẶT LỊCH nhưng cần xác định đúng Cố vấn phụ trách trước (Multi-step)
        if "đặt lịch" in intent_lower and ("cố vấn của" in intent_lower or "cố vấn của mình" in intent_lower or "đúng cố vấn" in intent_lower) \
                and not already_called_academic and not already_called_schedule:
            return {
                "type": "tool_call",
                "tool_name": "academic_query",
                "arguments": {"student_id": student_id},
                "thought": f"Cần xác định đúng Cố vấn học tập phụ trách sinh viên {student_id} trước khi đặt lịch. Tôi sẽ gọi tool academic_query trước."
            }

        # 3) Ý định ĐẶT LỊCH trực tiếp (đã biết hoặc không cần tra cứu Cố vấn)
        if "đặt lịch" in intent_lower and not already_called_schedule:
            return {
                "type": "tool_call",
                "tool_name": "schedule_appointment",
                "arguments": {"student_id": student_id, "datetime_str": datetime_str, "advisor_name": advisor_name},
                "thought": f"Đã đủ thông tin để đặt lịch. Tôi sẽ gọi tool schedule_appointment cho {student_id} với Cố vấn {advisor_name}."
            }

        # 4) Ý định tra cứu học vụ / GPA (chỉ kích hoạt khi có từ khóa tra cứu rõ ràng,
        # tránh gọi thừa Tool khi câu hỏi chỉ đơn thuần chứa mã sinh viên cho một Action khác)
        if ("tra cứu" in intent_lower or "gpa" in intent_lower) and not already_called_academic:
            return {
                "type": "tool_call",
                "tool_name": "academic_query",
                "arguments": {"student_id": student_id},
                "thought": f"Người dùng muốn tra cứu thông tin học vụ của sinh viên {student_id}. Tôi sẽ gọi tool academic_query."
            }

        # 5) Đã có Observation từ (các) bước trước -> tổng hợp câu trả lời cuối cùng
        if has_prior_observation:
            if "not_found" in prompt_lower:
                content = (
                    f"Rất tiếc, tôi không tìm thấy dữ liệu tương ứng với mã sinh viên '{student_id}' trong hệ thống. "
                    f"Bạn vui lòng kiểm tra lại mã sinh viên và thử lại."
                )
            else:
                content = (
                    "Tôi đã tổng hợp xong dữ liệu từ (các) công cụ tra cứu ở trên để trả lời chính xác yêu cầu của bạn "
                    "(xem chi tiết từng bước Observation trong Waterfall Trace Log)."
                )
            return {
                "type": "text",
                "content": content,
                "thought": "Đã nhận đủ Observation cần thiết từ MCP Server, tổng hợp câu trả lời cuối cùng cho sinh viên."
            }

        # 6) Câu hỏi chung, không cần gọi Tool
        return {
            "type": "text",
            "content": "[Mock Agent Response]: Xin chào! Quy chế học vụ VinUni yêu cầu sinh viên tích lũy tối thiểu 120 tín chỉ và duy trì GPA trên 2.0 để tốt nghiệp.",
            "thought": "Câu hỏi chung về quy chế học vụ, trả lời trực tiếp không cần gọi Tool."
        }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(model=self.model_name, contents=contents)
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("ℹ️ [Gemini Provider]: Chưa tìm thấy GEMINI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)
        
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            
            # Chuẩn hóa function declarations cho Gemini SDK
            function_declarations = []
            for tool in tools_schema:
                # Bỏ qua các tool schema chưa được định nghĩa hoàn chỉnh
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                function_declarations.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                })

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )

            # Kiểm tra xem Gemini có trả về Tool Call không
            if response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, 'args') and call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": f"Gemini quyết định gọi công cụ '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": response.text or "",
                    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }

        except Exception as e:
            print(f"⚠️ [Gemini API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (Native Tool Calling với OpenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("ℹ️ [OpenAI Provider]: Chưa tìm thấy OPENAI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"OpenAI quyết định gọi công cụ '{call.function.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }
        except Exception as e:
            print(f"⚠️ [OpenAI API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


def get_llm_provider() -> BaseLLMProvider:
    """Factory function khởi tạo Provider theo LLM_PROVIDER env variable"""
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if key and key != "your_gemini_api_key_here":
            return GeminiProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_api_key_here":
            return OpenAIProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "mock":
        return MockOfflineProvider()
    else:
        return MockOfflineProvider()
