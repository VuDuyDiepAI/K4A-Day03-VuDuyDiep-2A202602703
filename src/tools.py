"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
"""

import json
from typing import Dict, Any

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2)
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1: Đã được định nghĩa mẫu sẵn cho Học viên tham khảo
    {
        "name": "academic_query",
        "description": "Tra cứu hồ sơ và thông tin học vụ của sinh viên VinUni bằng mã sinh viên.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần tra cứu (ví dụ: 'SV2026001')"
                }
            },
            "required": ["student_id"]
        }
    },
    
    # --------------------------------------------------------------------------
    # TASK 1.2 (ĐÃ HOÀN THIỆN): TOOL SCHEMA CHO 'schedule_appointment'
    # Tool dùng để đặt lịch hẹn tư vấn học vụ với Cố vấn học tập VinUni.
    # --------------------------------------------------------------------------
    {
        "name": "schedule_appointment",
        "description": "Đặt lịch hẹn tư vấn học vụ với Cố vấn học tập VinUni.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần đặt lịch hẹn (ví dụ: 'SV2026001')"
                },
                "datetime_str": {
                    "type": "string",
                    "description": "Thời gian hẹn mong muốn, định dạng 'HH:MM DD/MM/YYYY' (ví dụ: '14:00 15/09/2026')"
                },
                "advisor_name": {
                    "type": "string",
                    "description": "Tên Cố vấn học tập (Academic Advisor) mà sinh viên muốn đặt lịch tư vấn (ví dụ: 'PGS.TS Nguyễn Văn A')"
                }
            },
            "required": ["student_id", "datetime_str", "advisor_name"]
        }
    },

    # --------------------------------------------------------------------------
    # 🆕 TOOL BỔ SUNG (KHÁC BIỆT SO VỚI BÀI MẪU): 'exam_schedule_query'
    # Đề tài đã chọn "Trợ lý Học vụ & Tra cứu Lịch thi VinUni" yêu cầu tra cứu
    # LỊCH THI bên cạnh GPA và đặt lịch tư vấn, nên bổ sung thêm Tool thứ 3
    # để Agent có đủ năng lực đáp ứng trọn vẹn đề bài (thay vì chỉ dừng ở 2 Tool
    # như bộ khung mẫu ban đầu).
    # --------------------------------------------------------------------------
    {
        "name": "exam_schedule_query",
        "description": "Tra cứu lịch thi (ngày giờ, phòng thi, hình thức thi) của sinh viên VinUni theo mã sinh viên và tùy chọn theo mã học phần.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần tra cứu lịch thi (ví dụ: 'SV2026001')"
                },
                "course_code": {
                    "type": "string",
                    "description": "Mã học phần cần tra cứu lịch thi cụ thể (ví dụ: 'CS101'). Nếu không cung cấp, trả về toàn bộ lịch thi của sinh viên."
                }
            },
            "required": ["student_id"]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

MOCK_DATABASE = {
    "SV2026001": {
        "full_name": "Nguyễn Văn An",
        "class": "AI-K4",
        "gpa": 3.85,
        "email": "an.nv@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "PGS.TS Nguyễn Văn A"
    },
    "SV2026002": {
        "full_name": "Trần Thị Bình",
        "class": "AI-K4",
        "gpa": 3.60,
        "email": "binh.tt@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "TS. Lê Thị B"
    }
}


MOCK_EXAM_SCHEDULE = {
    "SV2026001": [
        {"course_code": "CS101", "course_name": "Nhập môn Lập trình", "exam_date": "20/09/2026", "exam_time": "08:00", "room": "P.301", "format": "Trắc nghiệm + Tự luận"},
        {"course_code": "MA201", "course_name": "Đại số Tuyến tính", "exam_date": "22/09/2026", "exam_time": "13:30", "room": "P.205", "format": "Tự luận"}
    ],
    "SV2026002": [
        {"course_code": "CS101", "course_name": "Nhập môn Lập trình", "exam_date": "20/09/2026", "exam_time": "08:00", "room": "P.302", "format": "Trắc nghiệm + Tự luận"}
    ]
}


def execute_academic_query(student_id: str) -> str:
    """Thực thi tra cứu học vụ theo mã sinh viên"""
    student = MOCK_DATABASE.get(student_id.strip().upper())
    if student:
        return json.dumps({
            "status": "SUCCESS",
            "student_id": student_id,
            "data": student
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy dữ liệu sinh viên có mã '{student_id}'"
        }, ensure_ascii=False)


def execute_schedule_appointment(student_id: str, datetime_str: str, advisor_name: str = "PGS.TS Nguyễn Văn A") -> str:
    """Thực thi đặt lịch hẹn tư vấn học vụ"""
    return json.dumps({
        "status": "SUCCESS",
        "booking_id": f"BK-{student_id}-99",
        "student_id": student_id,
        "datetime": datetime_str,
        "advisor": advisor_name,
        "message": f"Đặt lịch thành công cho sinh viên {student_id} với {advisor_name} vào lúc {datetime_str}."
    }, ensure_ascii=False)


def execute_exam_schedule_query(student_id: str, course_code: str = None) -> str:
    """Thực thi tra cứu lịch thi theo mã sinh viên (và tùy chọn theo mã học phần)"""
    sid = student_id.strip().upper()
    schedule = MOCK_EXAM_SCHEDULE.get(sid)

    if not schedule:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy lịch thi nào cho sinh viên có mã '{student_id}'"
        }, ensure_ascii=False)

    if course_code:
        matched = [e for e in schedule if e["course_code"].strip().upper() == course_code.strip().upper()]
        if not matched:
            return json.dumps({
                "status": "NOT_FOUND",
                "message": f"Không tìm thấy lịch thi học phần '{course_code}' cho sinh viên '{student_id}'"
            }, ensure_ascii=False)
        schedule = matched

    return json.dumps({
        "status": "SUCCESS",
        "student_id": student_id,
        "exams": schedule
    }, ensure_ascii=False)


# Router gọi tool thực tế
TOOL_ROUTER = {
    "academic_query": execute_academic_query,
    "schedule_appointment": execute_schedule_appointment,
    "exam_schedule_query": execute_exam_schedule_query
}

def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)
