"""
🚀 CORE AGENT APPLICATION (DAY 03: CHATBOT VS REACT AGENT)
Thực thi so sánh giữa Chatbot Baseline (Cấp 2) và ReAct Agent kết nối MCP Server (Cấp 3).
"""

import json
import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from mcp_server import MCPAcademicServer
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_AGENT_SYSTEM_PROMPT,
    MAX_ITERATIONS
)
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Tải danh sách 5 test cases từ config/test_cases.json hoặc config/test_cases.example.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        example_path = os.path.join(base_dir, "config", "test_cases.example.json")
        if os.path.exists(example_path):
            print("⚠️ [CONFIG NOTICE]: Chưa thấy file 'config/test_cases.json'. Đang dùng mẫu 'config/test_cases.example.json'.")
            print("👉 Hãy chạy: copy config/test_cases.example.json config/test_cases.json và viết test cases theo đề tài của bạn!\n")
            config_path = example_path
        else:
            config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_waterfall_trace(trace_data: list):
    """Ghi vết log Waterfall Trace Log ra file docs/trace_waterfall.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    trace_path = os.path.join(docs_dir, "trace_waterfall.json")
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, ensure_ascii=False, indent=2)
    print(f"📊 [OBSERVABILITY]: Đã lưu {len(trace_data)} sự kiện Waterfall Trace tại '{trace_path}'!")


def run_baseline_chatbot(user_query: str, provider):
    """Chạy Chatbot gốc (Cấp 2) không có công cụ gọi Tool"""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot phản hồi:\n{response}")


def _summarize_observation(tool_name: str, obs_data: dict) -> str:
    """Tổng hợp 1 câu diễn giải ngắn gọn cho Observation trả về từ một Tool cụ thể,
    dùng làm phương án dự phòng (fallback) khi bước cuối cùng vẫn là TOOL_EXECUTION."""
    if not obs_data:
        return "Chưa thể trả lời chi tiết do chưa nhận được dữ liệu từ MCP Server."

    status = obs_data.get("status")
    if status == "NOT_FOUND":
        return obs_data.get("message", "Không tìm thấy thông tin yêu cầu.")

    if status == "SUCCESS":
        if tool_name == "academic_query" and "data" in obs_data:
            d = obs_data["data"]
            return (
                f"Kết quả tra cứu cho sinh viên {obs_data.get('student_id', '')} ({d.get('full_name', '')}): "
                f"Lớp {d.get('class', '')}, GPA: {d.get('gpa', '')}, Email: {d.get('email', '')}, "
                f"Trạng thái: {d.get('status', '')}, Cố vấn: {d.get('advisor', '')}."
            )
        if tool_name == "exam_schedule_query" and "exams" in obs_data:
            exams_str = "; ".join(
                f"{e.get('course_code')} ({e.get('course_name')}) - {e.get('exam_date')} {e.get('exam_time')} "
                f"tại {e.get('room')} [{e.get('format')}]"
                for e in obs_data["exams"]
            )
            return f"Lịch thi của sinh viên {obs_data.get('student_id', '')}: {exams_str}."
        if "message" in obs_data:
            return obs_data["message"]

    return f"Phản hồi từ công cụ '{tool_name}': {json.dumps(obs_data, ensure_ascii=False)}"


def run_react_agent(user_query: str, provider, mcp_server: MCPAcademicServer) -> list:
    """
    [REACT AGENT LOOP - MULTI-STEP] Thực thi vòng lặp Thought -> Action -> Observation
    với MCP Server, có khả năng gọi NHIỀU Tool nối tiếp nhau (không dừng lại sau
    lượt Tool Call đầu tiên như bản mẫu tham khảo `ai_levels/level3_native_mcp_agent.py`).

    Cơ chế: Sau mỗi Observation, ta nạp lại toàn bộ "Waterfall Scratchpad"
    (các cặp Action/Observation trước đó) vào prompt gửi cho LLM ở lượt kế tiếp,
    để LLM có đủ ngữ cảnh quyết định: (a) gọi tiếp Tool khác, hoặc (b) tổng hợp
    Final Answer khi đã đủ dữ liệu — đúng tinh thần Cấp độ 3 Native MCP Agent.

    Trả về danh sách trace log của phiên thực thi.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    step = 0
    trace_logs = []
    tools_list = mcp_server.list_tools()
    scratchpad_entries = []  # Lịch sử Action/Observation tích lũy qua các bước
    last_tool_name, last_obs_data = None, None

    while step < MAX_ITERATIONS:
        step += 1
        step_start_time = time.time()
        print(f"\n--- 🔄 Vòng lặp ReAct Loop (Step {step}/{MAX_ITERATIONS}) ---")

        # Ghép Scratchpad (nếu có) vào câu hỏi gốc để LLM suy luận đa bước
        if scratchpad_entries:
            scratchpad_text = "\n".join(scratchpad_entries)
            augmented_prompt = (
                f"{user_query}\n\n"
                f"[SCRATCHPAD]\n{scratchpad_text}\n[/SCRATCHPAD]\n\n"
                f"Dựa trên (các) Observation ở trên: nếu đã đủ dữ liệu để trả lời sinh viên, "
                f"hãy trả lời trực tiếp (type=text). Nếu vẫn còn thiếu dữ liệu, hãy tiếp tục gọi Tool phù hợp."
            )
        else:
            augmented_prompt = user_query

        # Gọi LLM với Native Tool Calling Specs
        llm_response = provider.generate_with_tools(augmented_prompt, tools_list, system_prompt=REACT_AGENT_SYSTEM_PROMPT)
        latency_ms = round((time.time() - step_start_time) * 1000, 2)

        thought = llm_response.get("thought", "Đang suy luận...")
        print(f"🧠 [Thought]: {thought}")

        # Trường hợp 1: LLM quyết định trả lời bằng văn bản trực tiếp -> DỪNG vòng lặp
        if llm_response.get("type") == "text":
            final_content = llm_response.get("content", "")
            print(f"🏁 [Final Answer]: {final_content}")
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "thought": thought,
                "output": final_content,
                "latency_ms": latency_ms
            })
            return trace_logs

        # Trường hợp 2: LLM đề xuất gọi Tool (Action) -> Thực thi rồi TIẾP TỤC vòng lặp
        elif llm_response.get("type") == "tool_call":
            tool_name = llm_response.get("tool_name")
            arguments = llm_response.get("arguments", {})

            print(f"🛠️ [Action Proposed]: {tool_name}({arguments})")

            # Thực thi Tool qua MCP Server (JSON-RPC 2.0)
            mcp_result = mcp_server.call_tool(tool_name, arguments)
            obs_data = mcp_result.get("result", {})

            if not obs_data:
                print(f"👁️ [Observation từ MCP Server]: {{}}")
                print("⚠️ [CHÚ Ý]: MCP Server trả về kết quả rỗng! Kiểm tra TODO 2.1 trong 'src/mcp_server.py'.")
            else:
                print(f"👁️ [Observation từ MCP Server]: {json.dumps(obs_data, ensure_ascii=False)}")

            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "TOOL_EXECUTION",
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data,
                "latency_ms": latency_ms
            })

            # Ghi lại vào Scratchpad để LLM dùng làm ngữ cảnh cho bước kế tiếp
            scratchpad_entries.append(
                f"Step {step}: Thought={thought} | Action={tool_name}({json.dumps(arguments, ensure_ascii=False)}) "
                f"| Observation={json.dumps(obs_data, ensure_ascii=False)}"
            )
            last_tool_name, last_obs_data = tool_name, obs_data
            # KHÔNG break ở đây -> vòng lặp tiếp tục để LLM có cơ hội gọi thêm Tool
            # khác (ví dụ: tra cứu Cố vấn trước rồi mới đặt lịch hẹn) hoặc tổng hợp
            # Final Answer ở lượt kế tiếp.
            continue

    # Nếu chạm giới hạn MAX_ITERATIONS mà LLM vẫn chưa trả lời bằng văn bản,
    # tự tổng hợp một Final Answer dự phòng từ Observation gần nhất để không bỏ trống câu trả lời.
    fallback_answer = _summarize_observation(last_tool_name, last_obs_data)
    print(f"\n⏱️ [MAX_ITERATIONS ĐẠT NGƯỠNG]: Tự tổng hợp Final Answer dự phòng từ Observation gần nhất.")
    print(f"🏁 [Final Answer]: {fallback_answer}")
    trace_logs.append({
        "step": step + 1,
        "query": user_query,
        "action_type": "FINAL_ANSWER",
        "thought": "Đã đạt giới hạn MAX_ITERATIONS, tổng hợp câu trả lời từ Observation gần nhất.",
        "output": fallback_answer,
        "latency_ms": 10.0
    })
    return trace_logs


if __name__ == "__main__":
    print("==========================================================")
    print("🏫 VINUNI AI COURSE - DAY 03 LAB: CHATBOT VS REACT AGENT")
    print("==========================================================")
    
    provider = get_llm_provider()
    mcp_server = MCPAcademicServer()
    
    print(f"🔌 LLM Provider: {provider.__class__.__name__}")
    print(f"🌐 MCP Server: {mcp_server.server_name}\n")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases thử nghiệm.\n")
    
    if "--interactive" in sys.argv:
        print("🎮 [INTERACTIVE MODE] Trò chuyện trực tiếp với ReAct Agent:")
        print("💡 Gợi ý câu hỏi thử nghiệm:")
        print("   - Câu hỏi chung: 'Quy chế học vụ VinUni yêu cầu bao nhiêu tín chỉ?'")
        print("   - Tra cứu học vụ: 'Hãy tra cứu thông tin học vụ của sinh viên SV2026001'")
        print("   - Đặt lịch hẹn: 'Đặt lịch hẹn tư vấn cho SV2026001 vào 14:00 ngày 15/09/2026'")
        print("   - Gõ 'exit' hoặc 'quit' để kết thúc phiên trò chuyện.\n")
        while True:
            try:
                user_input = input("👤 Sinh viên hỏi: ").strip()
                if not user_input or user_input.lower() in ["exit", "quit"]:
                    print("👋 Tạm biệt! Kết thúc phiên trò chuyện.")
                    break
                logs = run_react_agent(user_input, provider, mcp_server)
                save_waterfall_trace(logs)
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Đã thoát phiên tương tác.")
                break
    elif "--all" in sys.argv:
        print("🚀 [TEST SUITE MODE] Kiểm tra 5 Test Cases:")
        completed_count = 0
        todo_count = 0
        all_traces = []
        
        for tc in tests:
            print(f"\n==================================================")
            print(f"🧪 [{tc['id']}] Loại test: {tc['type']} (Độ phức tạp: {tc['complexity']})")
            print(f"📌 Kỳ vọng: {tc['expected_behavior']}")
            
            if tc["question"].strip().startswith("TODO"):
                print(f"⏸️ [CHƯA KÍCH HOẠT - ĐANG LÀ TODO]:")
                print(f"   {tc['question']}")
                print(f"   👉 Hãy mở file 'config/test_cases.json' để viết câu hỏi thực tế cho Test Case này!")
                todo_count += 1
            else:
                logs = run_react_agent(tc["question"], provider, mcp_server)
                all_traces.extend(logs)
                completed_count += 1
                
        print(f"\n==================================================")
        print(f"📊 [KẾT QUẢ TEST SUITE]: Đã thực thi {completed_count}/{len(tests)} Test Cases | {todo_count} Test Cases đang chờ điền câu hỏi (TODO)")
        if all_traces:
            save_waterfall_trace(all_traces)
        print(f"💡 Để trò chuyện trực tiếp từng câu: Chạy 'python src/app.py --interactive'")
    else:
        # Chế độ mặc định khi chỉ gõ 'python src/app.py'
        print("ℹ️ HƯỚNG DẪN SỬ DỤNG CHƯƠNG TRÌNH:")
        print("  1. Chat trực tiếp liên tục:   python src/app.py --interactive")
        print("  2. Chạy toàn bộ Test Cases:    python src/app.py --all\n")
        
        sample_query = tests[1]["question"]
        print(f"--- 🏁 DEMO CHẠY THỬ 1 TEST CASE MẪU (TC02: Tra cứu học vụ) ---")
        logs = run_react_agent(sample_query, provider, mcp_server)
        save_waterfall_trace(logs)
        print("\n💡 Hãy thử ngay lệnh: python src/app.py --interactive để chat trực tiếp!")
