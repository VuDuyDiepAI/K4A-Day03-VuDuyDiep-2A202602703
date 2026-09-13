# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** [Điền Họ và Tên]  
> **Mã Sinh Viên / Mã Học viên:** [Điền MSSV]  
> **Chủ đề Lựa chọn:** [Điền tên chủ đề đã chọn từ docs/DANH_SACH_DE_TAI.md hoặc Đề tài Mở]  

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | / 5 | Bài toán có yêu cầu chia nhỏ nhiều bước suy luận nối tiếp nhau không? |
| **2. Tool Interaction** | / 5 | Hệ thống có cần kết nối với MCP Server / Cơ sở dữ liệu bên ngoài không? |
| **3. Dynamic Decision** | / 5 | Bước tiếp theo có phụ thuộc vào kết quả quan sát bước trước không? |
| **4. Long Horizon Goal** | / 5 | Hệ thống có phải giữ mục tiêu xuyên suốt qua nhiều lượt xử lý không? |
| **TỔNG ĐIỂM AGENTIC FIT** | **/ 20** | *Nếu tổng điểm > 12/20: Bài toán rất phù hợp triển khai Agentic System.* |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật:

```json
[
  {
    "step": 1,
    "query": "Sinh viên SV2026002 muốn tra cứu lịch thi môn CS101, sau đó đặt lịch hẹn tư vấn với đúng cố vấn của mình vào lúc 09:00 ngày 21/09/2026",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "exam_schedule_query",
    "arguments": {
      "course_code": "CS101",
      "student_id": "SV2026002"
    },
    "observation": {
      "status": "SUCCESS",
      "student_id": "SV2026002",
      "exams": [
        {
          "course_code": "CS101",
          "course_name": "Nhập môn Lập trình",
          "exam_date": "20/09/2026",
          "exam_time": "08:00",
          "room": "P.302",
          "format": "Trắc nghiệm + Tự luận"
        }
      ]
    },
    "latency_ms": 4053.04
  },
  {
    "step": 2,
    "query": "Sinh viên SV2026002 muốn tra cứu lịch thi môn CS101, sau đó đặt lịch hẹn tư vấn với đúng cố vấn của mình vào lúc 09:00 ngày 21/09/2026",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "academic_query",
    "arguments": {
      "student_id": "SV2026002"
    },
    "observation": {
      "status": "SUCCESS",
      "student_id": "SV2026002",
      "data": {
        "full_name": "Trần Thị Bình",
        "class": "AI-K4",
        "gpa": 3.6,
        "email": "binh.tt@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "TS. Lê Thị B"
      }
    },
    "latency_ms": 3249.15
  },
  {
    "step": 3,
    "query": "Sinh viên SV2026002 muốn tra cứu lịch thi môn CS101, sau đó đặt lịch hẹn tư vấn với đúng cố vấn của mình vào lúc 09:00 ngày 21/09/2026",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "schedule_appointment",
    "arguments": {
      "datetime_str": "09:00 21/09/2026",
      "advisor_name": "TS. Lê Thị B",
      "student_id": "SV2026002"
    },
    "observation": {
      "status": "SUCCESS",
      "booking_id": "BK-SV2026002-99",
      "student_id": "SV2026002",
      "datetime": "09:00 21/09/2026",
      "advisor": "TS. Lê Thị B",
      "message": "Đặt lịch thành công cho sinh viên SV2026002 với TS. Lê Thị B vào lúc 09:00 21/09/2026."
    },
    "latency_ms": 3967.56
  },
  {
    "step": 4,
    "query": "Sinh viên SV2026002 muốn tra cứu lịch thi môn CS101, sau đó đặt lịch hẹn tư vấn với đúng cố vấn của mình vào lúc 09:00 ngày 21/09/2026",
    "action_type": "FINAL_ANSWER",
    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ).",
    "output": "Chào bạn, \n\nDưới đây là thông tin tra cứu lịch thi và kết quả đặt lịch hẹn tư vấn cho sinh viên **SV2026002 (Trần Thị Bình)**:\n\n### 1. Thông tin lịch thi môn CS101 (Nhập môn Lập trình)\n* **Tên học phần:** Nhập môn Lập trình (CS101)\n* **Ngày thi:** 20/09/2026\n* **Giờ thi:** 08:00\n* **Phòng thi:** P.302\n* **Hình thức thi:** Trắc nghiệm + Tự luận\n\n---\n\n### 2. Xác nhận đặt lịch hẹn tư vấn học vụ\n* **Cố vấn học tập phụ trách:** TS. Lê Thị B\n* **Thời gian hẹn:** 09:00 ngày 21/09/2026\n* **Mã đặt lịch (Booking ID):** BK-SV2026002-99\n* **Trạng thái:** **Đặt lịch thành công**\n\nChúc bạn ôn tập tốt và có buổi tư vấn hiệu quả! Nếu cần hỗ trợ thêm thông tin gì khác, bạn hãy báo cho trợ lý nhé.",
    "latency_ms": 5287.11
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [ ] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI).
- **Tổng số Test Cases đã chạy thành công:** ___ / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** ___ lượt.
- **Kết quả đẩy Repo nộp bài:** [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
