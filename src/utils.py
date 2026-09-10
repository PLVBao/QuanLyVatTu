import pandas as pd
from typing import Any, Optional

def format_quantity(value: Any, unit: Optional[str] = None, show_plus: bool = False) -> str:
    """
    Chuẩn hóa định dạng hiển thị số lượng vật tư toàn hệ thống:
    - Nếu là số nguyên hoặc số thực không có phần thập phân (465.00, 10.00, 200.00):
      loại bỏ phần thập phân không cần thiết (.00) -> 465, 10, 200.
    - Nếu là số thực có phần thập phân (10.50, 5.25):
      giữ tối đa 2 chữ số thập phân -> 10.50, 5.25.
    - Có định dạng phân tách hàng nghìn (1,000, 50,000).
    - Hỗ trợ kèm đơn vị tính (unit): format_quantity(465, "cây") -> "465 cây".
    - Hỗ trợ hiển thị dấu cộng (show_plus): format_quantity(15, show_plus=True) -> "+15".
    """
    if value is None or pd.isna(value) or value == "":
        res = "0"
    else:
        try:
            num = float(value)
            # Kiểm tra nếu số thực không có phần thập phân
            if abs(num - round(num)) < 1e-6:
                int_val = int(round(num))
                res = f"{int_val:,}"
                if show_plus and int_val > 0:
                    res = f"+{res}"
            else:
                res = f"{num:,.2f}"
                if show_plus and num > 0:
                    res = f"+{res}"
        except (ValueError, TypeError):
            res = str(value)

    if unit:
        return f"{res} {str(unit).strip()}".strip()
    return res


def apply_quantity_format(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """
    Áp dụng format_quantity cho danh sách các cột số lượng trong DataFrame trước khi hiển thị.
    Bảo toàn kiểu dữ liệu gốc bằng cách tạo bản sao và định dạng chuỗi hiển thị chuyên nghiệp.
    """
    df_copy = df.copy()
    for col in columns:
        if col in df_copy.columns:
            df_copy[col] = df_copy[col].apply(lambda x: format_quantity(x))
    return df_copy

