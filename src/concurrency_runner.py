import time
import threading
from datetime import datetime
import streamlit as st
import pandas as pd
from database import get_connection, execute_query, execute_non_query, reset_database_data
from src.utils import format_quantity, apply_quantity_format

def render_status_badge(text: str, state: str = "idle") -> str:
    """Tạo badge trạng thái trực quan dạng viên thuốc chuẩn Tailwind UI."""
    color_map = {
        "idle": ("#F1F5F9", "#475569", "#CBD5E1"),
        "running": ("#EFF6FF", "#1D4ED8", "#BFDBFE"),
        "waiting": ("#FFFBEB", "#B45309", "#FDE68A"),
        "blocked": ("#FEF3C7", "#D97706", "#FCD34D"),
        "success": ("#ECFDF5", "#047857", "#A7F3D0"),
        "error": ("#FEF2F2", "#B91C1C", "#FECACA")
    }
    bg, fg, border = color_map.get(state, color_map["idle"])
    return f"""<div style="display:inline-flex; align-items:center; gap:6px; padding:3px 10px; border-radius:9999px; background-color:{bg}; color:{fg}; border:1px solid {border}; font-size:12px; font-weight:600; margin-bottom:8px;">
        <span style="width:6px; height:6px; border-radius:50%; background-color:{fg}; display:inline-block;"></span>
        {text}
    </div>"""


def run_lost_update_dual(mode: str, s1_status_box, s1_log_box, s2_status_box, s2_log_box):
    """Kịch bản 1: Mất cập nhật (Lost Update) - Mô phỏng 2 phiên song song."""
    s1_logs = []
    s2_logs = []
    lock_hint = "WITH (UPDLOCK)" if mode == "fixed" else ""

    execute_non_query("UPDATE TON_KHO SET SoLuongTon = 465.00 WHERE MaKho = 'KHO01' AND MaVT = 'VT01'")

    s1_status_box.markdown(render_status_badge("Đang khởi tạo giao tác...", "running"), unsafe_allow_html=True)
    s2_status_box.markdown(render_status_badge("Đang chờ phiên 1 (trễ 1s)...", "idle"), unsafe_allow_html=True)

    def worker_session1():
        conn = None
        try:
            conn = get_connection()
            conn.autocommit = True
            cursor = conn.cursor()
            now = datetime.now().strftime("%H:%M:%S")
            s1_logs.append(f"[{now}] Bắt đầu giao tác: BEGIN TRANSACTION")
            s1_logs.append(f"[{now}] Thao tác: Xuất 15 cây Thép phi 10 tại KHO01.")
            cursor.execute("BEGIN TRANSACTION")

            cursor.execute(f"SELECT SoLuongTon FROM TON_KHO {lock_hint} WHERE MaKho = 'KHO01' AND MaVT = 'VT01'")
            row = cursor.fetchone()
            ton = float(row[0]) if row else 0.0
            now = datetime.now().strftime("%H:%M:%S")
            s1_logs.append(f"[{now}] Đọc tồn kho hiện tại: {ton:.2f} cây.")
            s1_logs.append(f"[{now}] Bắt đầu giữ khóa và kiểm kê thực địa (trễ 4.5s)...")
            s1_status_box.markdown(render_status_badge("Đang giữ khóa (trễ 4.5s)...", "running"), unsafe_allow_html=True)

            time.sleep(4.5)

            new_ton = ton - 15.0
            now = datetime.now().strftime("%H:%M:%S")
            s1_logs.append(f"[{now}] Hết trễ: Cập nhật tồn = {ton:.2f} - 15 = {new_ton:.2f}")
            cursor.execute("UPDATE TON_KHO SET SoLuongTon = ? WHERE MaKho = 'KHO01' AND MaVT = 'VT01'", (new_ton,))
            cursor.execute("COMMIT TRANSACTION")
            now = datetime.now().strftime("%H:%M:%S")
            s1_logs.append(f"[{now}] COMMIT TRANSACTION thành công! (Tồn ghi nhận: {new_ton:.2f})")
            s1_status_box.markdown(render_status_badge("Hoàn tất (COMMIT)", "success"), unsafe_allow_html=True)
        except Exception as e:
            if conn:
                try: cursor.execute("ROLLBACK TRANSACTION")
                except: pass
            s1_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Lỗi: {e}")
            s1_status_box.markdown(render_status_badge("Bị lỗi giao tác", "error"), unsafe_allow_html=True)
        finally:
            if conn: conn.close()

    def worker_session2():
        time.sleep(1.0)
        conn = None
        try:
            now = datetime.now().strftime("%H:%M:%S")
            s2_status_box.markdown(render_status_badge("Đang gửi yêu cầu nhập 50 cây...", "running"), unsafe_allow_html=True)
            s2_logs.append(f"[{now}] Bắt đầu giao tác: BEGIN TRANSACTION")
            s2_logs.append(f"[{now}] Thao tác: Nhập 50 cây Thép phi 10 vào KHO01.")
            conn = get_connection()
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION")

            t0 = time.time()
            if mode == "fixed":
                s2_status_box.markdown(render_status_badge("Bị chặn chờ khóa bởi Session 1...", "blocked"), unsafe_allow_html=True)
                s2_logs.append(f"[{now}] Gửi SELECT {lock_hint}... Bị chặn chờ khóa của Session 1!")

            cursor.execute(f"SELECT SoLuongTon FROM TON_KHO {lock_hint} WHERE MaKho = 'KHO01' AND MaVT = 'VT01'")
            row = cursor.fetchone()
            waited = time.time() - t0
            ton = float(row[0]) if row else 0.0
            now = datetime.now().strftime("%H:%M:%S")

            if waited > 1.0:
                s2_logs.append(f"[{now}] Đã nhận khóa sau {waited:.1f}s chờ Session 1 COMMIT.")
                s2_logs.append(f"[{now}] Đọc được tồn kho chính xác = {ton:.2f} cây.")
            else:
                s2_logs.append(f"[{now}] Đọc tồn kho hiện tại = {ton:.2f} cây (Không bị chặn).")

            s2_status_box.markdown(render_status_badge("Đang cập nhật tồn kho...", "running"), unsafe_allow_html=True)
            new_ton = ton + 50.0
            s2_logs.append(f"[{now}] Cập nhật tồn = {ton:.2f} + 50 = {new_ton:.2f}")
            cursor.execute("UPDATE TON_KHO SET SoLuongTon = ? WHERE MaKho = 'KHO01' AND MaVT = 'VT01'", (new_ton,))
            cursor.execute("COMMIT TRANSACTION")
            now = datetime.now().strftime("%H:%M:%S")
            s2_logs.append(f"[{now}] COMMIT TRANSACTION thành công! (Tồn ghi nhận: {new_ton:.2f})")
            s2_status_box.markdown(render_status_badge("Hoàn tất (COMMIT)", "success"), unsafe_allow_html=True)
        except Exception as e:
            if conn:
                try: cursor.execute("ROLLBACK TRANSACTION")
                except: pass
            s2_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Lỗi: {e}")
            s2_status_box.markdown(render_status_badge("Bị lỗi giao tác", "error"), unsafe_allow_html=True)
        finally:
            if conn: conn.close()

    t1 = threading.Thread(target=worker_session1)
    t2 = threading.Thread(target=worker_session2)
    t1.start()
    t2.start()

    while t1.is_alive() or t2.is_alive():
        time.sleep(0.25)
        s1_log_box.code("\n".join(s1_logs) if s1_logs else "Đang khởi tạo phiên làm việc...", language="log")
        s2_log_box.code("\n".join(s2_logs) if s2_logs else "Đang chờ đến lượt...", language="log")

    t1.join()
    t2.join()

    s1_log_box.code("\n".join(s1_logs), language="log")
    s2_log_box.code("\n".join(s2_logs), language="log")

    df_final = execute_query("SELECT SoLuongTon FROM TON_KHO WHERE MaKho = 'KHO01' AND MaVT = 'VT01'")
    final_stock = float(df_final.iloc[0]["SoLuongTon"]) if not df_final.empty else 0.0
    return final_stock


def run_dirty_read_dual(mode: str, s1_status_box, s1_log_box, s2_status_box, s2_log_box):
    """Kịch bản 2: Đọc dữ liệu rác (Dirty Read) - Mô phỏng 2 phiên song song."""
    s1_logs = []
    s2_logs = []
    iso_level = "READ UNCOMMITTED" if mode == "error" else "READ COMMITTED"

    execute_non_query("UPDATE TON_KHO SET SoLuongTon = 465.00 WHERE MaKho = 'KHO01' AND MaVT = 'VT01'")

    s1_status_box.markdown(render_status_badge("Đang khởi tạo giao tác...", "running"), unsafe_allow_html=True)
    s2_status_box.markdown(render_status_badge("Đang chờ phiên 1 (trễ 1s)...", "idle"), unsafe_allow_html=True)

    s2_val = {"read_value": None, "waited": 0.0}

    def worker_session1():
        conn = None
        try:
            conn = get_connection()
            conn.autocommit = True
            cursor = conn.cursor()
            now = datetime.now().strftime("%H:%M:%S")
            s1_logs.append(f"[{now}] Khởi tạo giao tác: BEGIN TRANSACTION")
            s1_logs.append(f"[{now}] Cập nhật tạm thời: UPDATE SoLuongTon = 999.00 cây...")
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute("UPDATE TON_KHO SET SoLuongTon = 999.00 WHERE MaKho = 'KHO01' AND MaVT = 'VT01'")

            now = datetime.now().strftime("%H:%M:%S")
            s1_logs.append(f"[{now}] Đã ghi tạm 999.00. Đang giữ Exclusive Lock (trễ 4.5s)...")
            s1_status_box.markdown(render_status_badge("Đang giữ khóa Exclusive (trễ 4.5s)...", "running"), unsafe_allow_html=True)

            time.sleep(4.5)

            now = datetime.now().strftime("%H:%M:%S")
            s1_logs.append(f"[{now}] Phát hiện sai lệch chứng từ -> Thực hiện ROLLBACK TRANSACTION!")
            cursor.execute("ROLLBACK TRANSACTION")
            now = datetime.now().strftime("%H:%M:%S")
            s1_logs.append(f"[{now}] Đã ROLLBACK hoàn tất. Số dư CSDL phục hồi về 465.00.")
            s1_status_box.markdown(render_status_badge("Đã ROLLBACK (Hủy bỏ)", "error"), unsafe_allow_html=True)
        except Exception as e:
            if conn:
                try: cursor.execute("ROLLBACK TRANSACTION")
                except: pass
            s1_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Lỗi: {e}")
            s1_status_box.markdown(render_status_badge("Bị lỗi giao tác", "error"), unsafe_allow_html=True)
        finally:
            if conn: conn.close()

    def worker_session2():
        time.sleep(1.0)
        conn = None
        try:
            now = datetime.now().strftime("%H:%M:%S")
            s2_logs.append(f"[{now}] Thiết lập mức cô lập: SET ISOLATION LEVEL {iso_level}")
            conn = get_connection()
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute(f"SET TRANSACTION ISOLATION LEVEL {iso_level}")

            if mode == "fixed":
                s2_status_box.markdown(render_status_badge("Bị chặn chờ khóa Exclusive...", "blocked"), unsafe_allow_html=True)
                s2_logs.append(f"[{now}] Gửi truy vấn SELECT... Bị chặn chờ Exclusive Lock của Session 1!")
            else:
                s2_status_box.markdown(render_status_badge("Đang đọc không khóa (Uncommitted)...", "running"), unsafe_allow_html=True)
                s2_logs.append(f"[{now}] Gửi truy vấn SELECT (Không kiểm tra khóa)...")

            t0 = time.time()
            cursor.execute("SELECT SoLuongTon FROM TON_KHO WHERE MaKho = 'KHO01' AND MaVT = 'VT01'")
            row = cursor.fetchone()
            waited = time.time() - t0
            val = float(row[0]) if row else None
            s2_val["read_value"] = val
            s2_val["waited"] = waited
            now = datetime.now().strftime("%H:%M:%S")

            if waited > 1.0:
                s2_logs.append(f"[{now}] Đã đọc sau {waited:.1f}s chờ Session 1 ROLLBACK.")
                s2_logs.append(f"[{now}] Đọc được số dư hợp lệ: {val:.2f} cây.")
                s2_status_box.markdown(render_status_badge(f"Hoàn tất (Đọc hợp lệ: {val:.2f})", "success"), unsafe_allow_html=True)
            else:
                s2_logs.append(f"[{now}] Đọc thành công ngay lập tức: {val:.2f} cây!")
                s2_logs.append(f"[{now}] CẢNH BÁO: Đọc phải giá trị ảo 999.00 trước khi Session 1 ROLLBACK!")
                s2_status_box.markdown(render_status_badge(f"Đọc phải dữ liệu rác ({val:.2f})", "error"), unsafe_allow_html=True)
        except Exception as e:
            s2_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Lỗi: {e}")
            s2_status_box.markdown(render_status_badge("Bị lỗi giao tác", "error"), unsafe_allow_html=True)
        finally:
            if conn: conn.close()

    t1 = threading.Thread(target=worker_session1)
    t2 = threading.Thread(target=worker_session2)
    t1.start()
    t2.start()

    while t1.is_alive() or t2.is_alive():
        time.sleep(0.25)
        s1_log_box.code("\n".join(s1_logs) if s1_logs else "Đang khởi tạo phiên làm việc...", language="log")
        s2_log_box.code("\n".join(s2_logs) if s2_logs else "Đang chờ đến lượt...", language="log")

    t1.join()
    t2.join()

    s1_log_box.code("\n".join(s1_logs), language="log")
    s2_log_box.code("\n".join(s2_logs), language="log")

    df_final = execute_query("SELECT SoLuongTon FROM TON_KHO WHERE MaKho = 'KHO01' AND MaVT = 'VT01'")
    final_stock = float(df_final.iloc[0]["SoLuongTon"]) if not df_final.empty else 0.0
    return s2_val["read_value"], final_stock


def run_non_repeatable_read_dual(mode: str, s1_status_box, s1_log_box, s2_status_box, s2_log_box):
    """Kịch bản 3: Không đọc lại được (Non-repeatable Read) - Mô phỏng 2 phiên song song."""
    s1_logs = []
    s2_logs = []
    iso_level = "READ COMMITTED" if mode == "error" else "REPEATABLE READ"

    execute_non_query("UPDATE TON_KHO SET SoLuongTon = 465.00 WHERE MaKho = 'KHO01' AND MaVT = 'VT01'")

    s1_status_box.markdown(render_status_badge("Đang khởi tạo giao tác...", "running"), unsafe_allow_html=True)
    s2_status_box.markdown(render_status_badge("Đang chờ phiên 1 (trễ 1s)...", "idle"), unsafe_allow_html=True)

    s1_vals = {"read1": None, "read2": None}

    def worker_session1():
        conn = None
        try:
            conn = get_connection()
            conn.autocommit = True
            cursor = conn.cursor()
            now = datetime.now().strftime("%H:%M:%S")
            s1_logs.append(f"[{now}] Thiết lập mức cô lập: SET ISOLATION LEVEL {iso_level}")
            s1_logs.append(f"[{now}] Khởi tạo giao tác: BEGIN TRANSACTION")
            cursor.execute(f"SET TRANSACTION ISOLATION LEVEL {iso_level}")
            cursor.execute("BEGIN TRANSACTION")

            cursor.execute("SELECT SoLuongTon FROM TON_KHO WHERE MaKho = 'KHO01' AND MaVT = 'VT01'")
            r1 = float(cursor.fetchone()[0])
            s1_vals["read1"] = r1
            now = datetime.now().strftime("%H:%M:%S")
            s1_logs.append(f"[{now}] Đọc lần 1: SoLuongTon = {r1:.2f} cây.")
            s1_logs.append(f"[{now}] Đang giữ Transaction và đối chiếu chứng từ (trễ 4.5s)...")
            s1_status_box.markdown(render_status_badge(f"Đọc Lần 1: {r1:.2f} (Trễ 4.5s)...", "running"), unsafe_allow_html=True)

            time.sleep(4.5)

            cursor.execute("SELECT SoLuongTon FROM TON_KHO WHERE MaKho = 'KHO01' AND MaVT = 'VT01'")
            r2 = float(cursor.fetchone()[0])
            s1_vals["read2"] = r2
            now = datetime.now().strftime("%H:%M:%S")
            s1_logs.append(f"[{now}] Đọc lần 2: SoLuongTon = {r2:.2f} cây.")
            cursor.execute("COMMIT TRANSACTION")
            s1_logs.append(f"[{now}] COMMIT TRANSACTION thành công.")

            if r1 == r2:
                s1_status_box.markdown(render_status_badge(f"Hoàn tất (Nhất quán {r2:.2f})", "success"), unsafe_allow_html=True)
            else:
                s1_status_box.markdown(render_status_badge(f"Hoàn tất (Bị lệch: {r1:.2f} -> {r2:.2f})", "error"), unsafe_allow_html=True)
        except Exception as e:
            if conn:
                try: cursor.execute("ROLLBACK TRANSACTION")
                except: pass
            s1_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Lỗi: {e}")
            s1_status_box.markdown(render_status_badge("Bị lỗi giao tác", "error"), unsafe_allow_html=True)
        finally:
            if conn: conn.close()

    def worker_session2():
        time.sleep(1.0)
        conn = None
        try:
            now = datetime.now().strftime("%H:%M:%S")
            s2_status_box.markdown(render_status_badge("Đang cập nhật +100 cây...", "running"), unsafe_allow_html=True)
            s2_logs.append(f"[{now}] Khởi tạo giao tác: BEGIN TRANSACTION")
            s2_logs.append(f"[{now}] Thao tác: Nhập bổ sung UPDATE SoLuongTon = SoLuongTon + 100...")
            conn = get_connection()
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION")

            t0 = time.time()
            if mode == "fixed":
                s2_status_box.markdown(render_status_badge("Bị chặn bởi Shared Lock của Session 1...", "blocked"), unsafe_allow_html=True)
                s2_logs.append(f"[{now}] Gửi lệnh UPDATE... Bị chặn chờ Shared Lock của Session 1 giải phóng!")

            cursor.execute("UPDATE TON_KHO SET SoLuongTon = SoLuongTon + 100 WHERE MaKho = 'KHO01' AND MaVT = 'VT01'")
            waited = time.time() - t0
            now = datetime.now().strftime("%H:%M:%S")

            if waited > 1.0:
                s2_logs.append(f"[{now}] Đã nhận khóa sau {waited:.1f}s chờ Session 1 COMMIT.")
            else:
                s2_logs.append(f"[{now}] Cập nhật thành công ngay lập tức giữa 2 lần đọc của Session 1!")

            cursor.execute("COMMIT TRANSACTION")
            s2_logs.append(f"[{now}] COMMIT TRANSACTION thành công (+100 cây).")
            s2_status_box.markdown(render_status_badge("Hoàn tất (COMMIT +100)", "success"), unsafe_allow_html=True)
        except Exception as e:
            if conn:
                try: cursor.execute("ROLLBACK TRANSACTION")
                except: pass
            s2_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Lỗi: {e}")
            s2_status_box.markdown(render_status_badge("Bị lỗi giao tác", "error"), unsafe_allow_html=True)
        finally:
            if conn: conn.close()

    t1 = threading.Thread(target=worker_session1)
    t2 = threading.Thread(target=worker_session2)
    t1.start()
    t2.start()

    while t1.is_alive() or t2.is_alive():
        time.sleep(0.25)
        s1_log_box.code("\n".join(s1_logs) if s1_logs else "Đang khởi tạo phiên làm việc...", language="log")
        s2_log_box.code("\n".join(s2_logs) if s2_logs else "Đang chờ đến lượt...", language="log")

    t1.join()
    t2.join()

    s1_log_box.code("\n".join(s1_logs), language="log")
    s2_log_box.code("\n".join(s2_logs), language="log")

    df_final = execute_query("SELECT SoLuongTon FROM TON_KHO WHERE MaKho = 'KHO01' AND MaVT = 'VT01'")
    final_stock = float(df_final.iloc[0]["SoLuongTon"]) if not df_final.empty else 0.0
    return s1_vals["read1"], s1_vals["read2"], final_stock


def run_deadlock_dual(mode: str, s1_status_box, s1_log_box, s2_status_box, s2_log_box):
    """Kịch bản 4: Khóa chết (Deadlock) - Mô phỏng 2 phiên song song."""
    s1_logs = []
    s2_logs = []

    execute_non_query("UPDATE TON_KHO SET SoLuongTon = 465.00 WHERE MaKho = 'KHO01' AND MaVT = 'VT01'")
    execute_non_query("UPDATE TON_KHO SET SoLuongTon = 10.00 WHERE MaKho = 'KHO02' AND MaVT = 'VT01'")

    s1_status_box.markdown(render_status_badge("Đang khởi tạo giao tác KHO01 -> KHO02...", "running"), unsafe_allow_html=True)
    s2_status_box.markdown(render_status_badge("Đang chờ phiên 1 (trễ 0.6s)...", "idle"), unsafe_allow_html=True)

    results = {"s1": None, "s2": None}

    if mode == "error":
        def s1_error():
            conn = None
            try:
                conn = get_connection()
                conn.autocommit = True
                cursor = conn.cursor()
                now = datetime.now().strftime("%H:%M:%S")
                s1_logs.append(f"[{now}] Bắt đầu BEGIN TRANSACTION...")
                s1_logs.append(f"[{now}] Bước 1: Khóa KHO01 (Trừ 5 cây VT01)...")
                cursor.execute("BEGIN TRANSACTION")
                cursor.execute("UPDATE TON_KHO SET SoLuongTon = SoLuongTon - 5 WHERE MaKho = 'KHO01' AND MaVT = 'VT01'")

                now = datetime.now().strftime("%H:%M:%S")
                s1_logs.append(f"[{now}] Đã khóa KHO01. Đang giữ khóa và xử lý (trễ 3.5s)...")
                s1_status_box.markdown(render_status_badge("Đã khóa KHO01, trễ 3.5s...", "running"), unsafe_allow_html=True)

                time.sleep(3.5)

                now = datetime.now().strftime("%H:%M:%S")
                s1_logs.append(f"[{now}] Bước 2: Yêu cầu khóa tiếp KHO02 (Cộng 5 cây VT01)...")
                s1_status_box.markdown(render_status_badge("Đang chờ khóa KHO02...", "waiting"), unsafe_allow_html=True)
                cursor.execute("UPDATE TON_KHO SET SoLuongTon = SoLuongTon + 5 WHERE MaKho = 'KHO02' AND MaVT = 'VT01'")
                cursor.execute("COMMIT TRANSACTION")

                now = datetime.now().strftime("%H:%M:%S")
                s1_logs.append(f"[{now}] COMMIT TRANSACTION thành công!")
                s1_status_box.markdown(render_status_badge("Hoàn tất (COMMIT)", "success"), unsafe_allow_html=True)
                results["s1"] = "COMMIT Thành công"
            except Exception as e:
                if conn:
                    try: cursor.execute("ROLLBACK TRANSACTION")
                    except: pass
                now = datetime.now().strftime("%H:%M:%S")
                s1_logs.append(f"[{now}] Lỗi Deadlock Victim: {e}")
                s1_status_box.markdown(render_status_badge("Bị hủy (Deadlock Victim Msg 1205)", "error"), unsafe_allow_html=True)
                results["s1"] = "Deadlock Victim (Msg 1205)"
            finally:
                if conn: conn.close()

        def s2_error():
            time.sleep(0.6)
            conn = None
            try:
                conn = get_connection()
                conn.autocommit = True
                cursor = conn.cursor()
                now = datetime.now().strftime("%H:%M:%S")
                s2_status_box.markdown(render_status_badge("Bắt đầu giao tác KHO02 -> KHO01...", "running"), unsafe_allow_html=True)
                s2_logs.append(f"[{now}] Bắt đầu BEGIN TRANSACTION...")
                s2_logs.append(f"[{now}] Bước 1: Khóa KHO02 (Trừ 2 cây VT01)...")
                cursor.execute("BEGIN TRANSACTION")
                cursor.execute("UPDATE TON_KHO SET SoLuongTon = SoLuongTon - 2 WHERE MaKho = 'KHO02' AND MaVT = 'VT01'")

                now = datetime.now().strftime("%H:%M:%S")
                s2_logs.append(f"[{now}] Đã khóa KHO02. Đang giữ khóa và xử lý (trễ 3.5s)...")
                s2_status_box.markdown(render_status_badge("Đã khóa KHO02, trễ 3.5s...", "running"), unsafe_allow_html=True)

                time.sleep(3.5)

                now = datetime.now().strftime("%H:%M:%S")
                s2_logs.append(f"[{now}] Bước 2: Yêu cầu khóa tiếp KHO01 (Cộng 2 cây VT01)...")
                s2_status_box.markdown(render_status_badge("Đang chờ khóa KHO01 (Xung đột chéo!)...", "blocked"), unsafe_allow_html=True)
                cursor.execute("UPDATE TON_KHO SET SoLuongTon = SoLuongTon + 2 WHERE MaKho = 'KHO01' AND MaVT = 'VT01'")
                cursor.execute("COMMIT TRANSACTION")

                now = datetime.now().strftime("%H:%M:%S")
                s2_logs.append(f"[{now}] COMMIT TRANSACTION thành công!")
                s2_status_box.markdown(render_status_badge("Hoàn tất (COMMIT)", "success"), unsafe_allow_html=True)
                results["s2"] = "COMMIT Thành công"
            except Exception as e:
                if conn:
                    try: cursor.execute("ROLLBACK TRANSACTION")
                    except: pass
                now = datetime.now().strftime("%H:%M:%S")
                s2_logs.append(f"[{now}] Lỗi Deadlock Victim: {e}")
                s2_status_box.markdown(render_status_badge("Bị hủy (Deadlock Victim Msg 1205)", "error"), unsafe_allow_html=True)
                results["s2"] = "Deadlock Victim (Msg 1205)"
            finally:
                if conn: conn.close()

        t1 = threading.Thread(target=s1_error)
        t2 = threading.Thread(target=s2_error)
    else:
        def s1_fixed():
            conn = None
            try:
                conn = get_connection()
                conn.autocommit = True
                cursor = conn.cursor()
                now = datetime.now().strftime("%H:%M:%S")
                s1_logs.append(f"[{now}] [LOCK ORDERING] Chuyển KHO01 -> KHO02. Yêu cầu khóa KHO01 trước (Trừ 5)...")
                cursor.execute("BEGIN TRANSACTION")
                cursor.execute("UPDATE TON_KHO SET SoLuongTon = SoLuongTon - 5 WHERE MaKho = 'KHO01' AND MaVT = 'VT01'")

                now = datetime.now().strftime("%H:%M:%S")
                s1_logs.append(f"[{now}] Đã khóa KHO01 thành công. Đang giữ khóa (trễ 3s)...")
                s1_status_box.markdown(render_status_badge("Đã khóa KHO01, giữ 3s...", "running"), unsafe_allow_html=True)

                time.sleep(3.0)

                now = datetime.now().strftime("%H:%M:%S")
                s1_logs.append(f"[{now}] Khóa tiếp KHO02 (Cộng 5 cây)...")
                cursor.execute("UPDATE TON_KHO SET SoLuongTon = SoLuongTon + 5 WHERE MaKho = 'KHO02' AND MaVT = 'VT01'")
                cursor.execute("COMMIT TRANSACTION")

                now = datetime.now().strftime("%H:%M:%S")
                s1_logs.append(f"[{now}] COMMIT TRANSACTION thành công!")
                s1_status_box.markdown(render_status_badge("Hoàn tất (COMMIT)", "success"), unsafe_allow_html=True)
                results["s1"] = "COMMIT Thành công"
            except Exception as e:
                if conn:
                    try: cursor.execute("ROLLBACK TRANSACTION")
                    except: pass
                s1_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Lỗi: {e}")
                s1_status_box.markdown(render_status_badge("Bị lỗi giao tác", "error"), unsafe_allow_html=True)
                results["s1"] = f"Lỗi: {e}"
            finally:
                if conn: conn.close()

        def s2_fixed():
            time.sleep(0.6)
            conn = None
            try:
                conn = get_connection()
                conn.autocommit = True
                cursor = conn.cursor()
                now = datetime.now().strftime("%H:%M:%S")
                s2_logs.append(f"[{now}] [LOCK ORDERING] Chuyển KHO02 -> KHO01. Tuân thủ thứ tự: Yêu cầu khóa KHO01 trước!")
                cursor.execute("BEGIN TRANSACTION")
                s2_status_box.markdown(render_status_badge("Chờ khóa KHO01 theo Lock Ordering...", "blocked"), unsafe_allow_html=True)

                t0 = time.time()
                cursor.execute("UPDATE TON_KHO SET SoLuongTon = SoLuongTon + 2 WHERE MaKho = 'KHO01' AND MaVT = 'VT01'")
                waited = time.time() - t0
                now = datetime.now().strftime("%H:%M:%S")
                s2_logs.append(f"[{now}] Đã nhận khóa KHO01 sau {waited:.1f}s chờ Session 1. Khóa tiếp KHO02 (Trừ 2)...")
                s2_status_box.markdown(render_status_badge("Đã nhận KHO01, đang khóa KHO02...", "running"), unsafe_allow_html=True)

                cursor.execute("UPDATE TON_KHO SET SoLuongTon = SoLuongTon - 2 WHERE MaKho = 'KHO02' AND MaVT = 'VT01'")
                cursor.execute("COMMIT TRANSACTION")

                now = datetime.now().strftime("%H:%M:%S")
                s2_logs.append(f"[{now}] COMMIT TRANSACTION thành công!")
                s2_status_box.markdown(render_status_badge("Hoàn tất (COMMIT)", "success"), unsafe_allow_html=True)
                results["s2"] = "COMMIT Thành công"
            except Exception as e:
                if conn:
                    try: cursor.execute("ROLLBACK TRANSACTION")
                    except: pass
                s2_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Lỗi: {e}")
                s2_status_box.markdown(render_status_badge("Bị lỗi giao tác", "error"), unsafe_allow_html=True)
                results["s2"] = f"Lỗi: {e}"
            finally:
                if conn: conn.close()

        t1 = threading.Thread(target=s1_fixed)
        t2 = threading.Thread(target=s2_fixed)

    t1.start()
    t2.start()

    while t1.is_alive() or t2.is_alive():
        time.sleep(0.25)
        s1_log_box.code("\n".join(s1_logs) if s1_logs else "Đang khởi tạo phiên làm việc...", language="log")
        s2_log_box.code("\n".join(s2_logs) if s2_logs else "Đang chờ đến lượt...", language="log")

    t1.join()
    t2.join()

    s1_log_box.code("\n".join(s1_logs), language="log")
    s2_log_box.code("\n".join(s2_logs), language="log")

    df_k1 = execute_query("SELECT SoLuongTon FROM TON_KHO WHERE MaKho = 'KHO01' AND MaVT = 'VT01'")
    df_k2 = execute_query("SELECT SoLuongTon FROM TON_KHO WHERE MaKho = 'KHO02' AND MaVT = 'VT01'")
    final_k1 = float(df_k1.iloc[0]["SoLuongTon"]) if not df_k1.empty else 0.0
    final_k2 = float(df_k2.iloc[0]["SoLuongTon"]) if not df_k2.empty else 0.0
    return results, final_k1, final_k2


def run_phantom_read_dual(mode: str, s1_status_box, s1_log_box, s2_status_box, s2_log_box):
    """Kịch bản 5: Đọc bóng ma (Phantom Read) - Mô phỏng 2 phiên song song."""
    s1_logs = []
    s2_logs = []
    iso_level = "REPEATABLE READ" if mode == "error" else "SERIALIZABLE"

    # Đảm bảo dữ liệu chuẩn tại KHO02: Xóa VT02 (nếu có từ phiên trước) và đảm bảo VT01 có tồn 10 <= 50 (dưới tối thiểu)
    execute_non_query("DELETE FROM TON_KHO WHERE MaKho = 'KHO02' AND MaVT = 'VT02'")
    execute_non_query("""
        IF NOT EXISTS (SELECT 1 FROM TON_KHO WHERE MaKho = 'KHO02' AND MaVT = 'VT01')
            INSERT INTO TON_KHO (MaKho, MaVT, SoLuongTon) VALUES ('KHO02', 'VT01', 10.00)
        ELSE
            UPDATE TON_KHO SET SoLuongTon = 10.00 WHERE MaKho = 'KHO02' AND MaVT = 'VT01'
    """)

    s1_status_box.markdown(render_status_badge("Đang khởi tạo giao tác kiểm tra cảnh báo...", "running"), unsafe_allow_html=True)
    s2_status_box.markdown(render_status_badge("Đang chờ phiên 1 (trễ 1s)...", "idle"), unsafe_allow_html=True)

    s1_vals = {"read1": None, "read2": None}

    def worker_session1():
        conn = None
        try:
            conn = get_connection()
            conn.autocommit = True
            cursor = conn.cursor()
            now = datetime.now().strftime("%H:%M:%S")
            s1_logs.append(f"[{now}] Thiết lập mức cô lập: SET ISOLATION LEVEL {iso_level}")
            s1_logs.append(f"[{now}] Khởi tạo giao tác: BEGIN TRANSACTION")
            cursor.execute(f"SET TRANSACTION ISOLATION LEVEL {iso_level}")
            cursor.execute("BEGIN TRANSACTION")

            sql_check = """
                SELECT COUNT(*) 
                FROM TON_KHO tk 
                JOIN VAT_TU vt ON tk.MaVT = vt.MaVT 
                WHERE tk.MaKho = 'KHO02' AND tk.SoLuongTon <= vt.TonToiThieu
            """
            cursor.execute(sql_check)
            r1 = int(cursor.fetchone()[0])
            s1_vals["read1"] = r1
            now = datetime.now().strftime("%H:%M:%S")
            s1_logs.append(f"[{now}] Đọc lần 1: Đếm được {r1} mặt hàng dưới mức tối thiểu tại KHO02 (VT01: tồn 10 <= định mức 50).")
            s1_logs.append(f"[{now}] Đang giữ Transaction và lập báo cáo kế hoạch mua sắm (trễ 4.5s)...")
            s1_status_box.markdown(render_status_badge(f"Lần 1: {r1} mặt hàng (Trễ 4.5s)...", "running"), unsafe_allow_html=True)

            time.sleep(4.5)

            cursor.execute(sql_check)
            r2 = int(cursor.fetchone()[0])
            s1_vals["read2"] = r2
            now = datetime.now().strftime("%H:%M:%S")
            s1_logs.append(f"[{now}] Đọc lần 2: Đếm được {r2} mặt hàng thỏa điều kiện.")
            cursor.execute("COMMIT TRANSACTION")
            s1_logs.append(f"[{now}] COMMIT TRANSACTION thành công.")

            if r1 == r2:
                s1_status_box.markdown(render_status_badge(f"Hoàn tất (Nhất quán {r2} mặt hàng)", "success"), unsafe_allow_html=True)
            else:
                s1_status_box.markdown(render_status_badge(f"Bóng ma xuất hiện ({r1} -> {r2} mặt hàng)", "error"), unsafe_allow_html=True)
        except Exception as e:
            if conn:
                try: cursor.execute("ROLLBACK TRANSACTION")
                except: pass
            s1_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Lỗi: {e}")
            s1_status_box.markdown(render_status_badge("Bị lỗi giao tác", "error"), unsafe_allow_html=True)
        finally:
            if conn: conn.close()

    def worker_session2():
        time.sleep(1.0)
        conn = None
        try:
            now = datetime.now().strftime("%H:%M:%S")
            s2_status_box.markdown(render_status_badge("Đang gửi yêu cầu nhập mặt hàng mới...", "running"), unsafe_allow_html=True)
            s2_logs.append(f"[{now}] Khởi tạo giao tác: BEGIN TRANSACTION")
            s2_logs.append(f"[{now}] Thao tác: Nhập 15 bao Xi măng (VT02 <= định mức 100) vào KHO02...")
            conn = get_connection()
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION")

            t0 = time.time()
            if mode == "fixed":
                s2_status_box.markdown(render_status_badge("Bị chặn bởi Range Lock của Session 1...", "blocked"), unsafe_allow_html=True)
                s2_logs.append(f"[{now}] Gửi lệnh INSERT... Bị chặn chờ Range Lock của Session 1 giải phóng!")

            cursor.execute("INSERT INTO TON_KHO (MaKho, MaVT, SoLuongTon) VALUES ('KHO02', 'VT02', 15.00)")
            waited = time.time() - t0
            now = datetime.now().strftime("%H:%M:%S")

            if waited > 1.0:
                s2_logs.append(f"[{now}] Đã nhận khóa chèn sau {waited:.1f}s chờ Session 1 COMMIT.")
            else:
                s2_logs.append(f"[{now}] Chèn thành công ngay lập tức: Mặt hàng mới VT02 xuất hiện giữa 2 lần đọc của Session 1!")

            cursor.execute("COMMIT TRANSACTION")
            s2_logs.append(f"[{now}] COMMIT TRANSACTION thành công (+1 dòng mới).")
            s2_status_box.markdown(render_status_badge("Hoàn tất (COMMIT)", "success"), unsafe_allow_html=True)
        except Exception as e:
            if conn:
                try: cursor.execute("ROLLBACK TRANSACTION")
                except: pass
            s2_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Lỗi: {e}")
            s2_status_box.markdown(render_status_badge("Bị lỗi giao tác", "error"), unsafe_allow_html=True)
        finally:
            if conn: conn.close()

    t1 = threading.Thread(target=worker_session1)
    t2 = threading.Thread(target=worker_session2)
    t1.start()
    t2.start()

    while t1.is_alive() or t2.is_alive():
        time.sleep(0.25)
        s1_log_box.code("\n".join(s1_logs) if s1_logs else "Đang khởi tạo phiên làm việc...", language="log")
        s2_log_box.code("\n".join(s2_logs) if s2_logs else "Đang chờ đến lượt...", language="log")

    t1.join()
    t2.join()

    s1_log_box.code("\n".join(s1_logs), language="log")
    s2_log_box.code("\n".join(s2_logs), language="log")

    df_final = execute_query("""
        SELECT COUNT(*) AS Cnt 
        FROM TON_KHO tk 
        JOIN VAT_TU vt ON tk.MaVT = vt.MaVT 
        WHERE tk.MaKho = 'KHO02' AND tk.SoLuongTon <= vt.TonToiThieu
    """)
    final_cnt = int(df_final.iloc[0]["Cnt"]) if not df_final.empty else 0

    # Dọn dẹp dòng tạm VT02 để bảo toàn CSDL mẫu
    execute_non_query("DELETE FROM TON_KHO WHERE MaKho = 'KHO02' AND MaVT = 'VT02'")

    return s1_vals["read1"], s1_vals["read2"], final_cnt


def render_concurrency_demo_ui():
    """Giao diện Chuyên đề: Kiểm thử Giao tác & Điều khiển Tương tranh song song (Dual-User Simulation - Chỉ dành cho QUAN_LY)."""
    from src.auth import is_manager, render_access_denied
    if not is_manager():
        render_access_denied("Kiểm thử giao tác & Điều khiển tương tranh")
        return

    st.title("Kiểm thử giao tác & Điều khiển tương tranh")
    st.caption("Mô phỏng thực nghiệm 2 người dùng thao tác song song trên Microsoft SQL Server")

    col_t1, col_t2 = st.columns([2.5, 1.5])
    with col_t1:
        st.markdown("""
        **Đối tượng kiểm thử:** Vật tư `VT01` (Thép phi 10) tại kho `KHO01` và `KHO02`.  
        **Số dư chuẩn ban đầu:** `KHO01` = 465.00 cây, `KHO02` = 10.00 cây.
        """)
    with col_t2:
        if st.button("Khôi phục CSDL & Số dư mẫu", use_container_width=True, type="secondary"):
            ok, msg = reset_database_data()
            if ok:
                st.success("Đã khôi phục toàn bộ CSDL và số dư mẫu ban đầu.")
                st.rerun()
            else:
                st.error(f"Lỗi: {msg}")

    df_curr = execute_query("SELECT MaKho, MaVT, SoLuongTon FROM TON_KHO WHERE MaVT = 'VT01'")
    df_curr_disp = apply_quantity_format(df_curr, ["SoLuongTon"])
    st.dataframe(
        df_curr_disp,
        use_container_width=True,
        hide_index=True,
        column_config={
            "MaKho": "Mã kho",
            "MaVT": "Mã vật tư",
            "SoLuongTon": "Số lượng tồn hiện thời"
        }
    )

    st.write("---")

    selected_exp = st.selectbox(
        "Kịch bản thực nghiệm tương tranh",
        [
            "1. Mất cập nhật (Lost Update) - Khắc phục bằng WITH (UPDLOCK)",
            "2. Đọc dữ liệu rác (Dirty Read) - Khắc phục bằng READ COMMITTED",
            "3. Không đọc lại được (Non-repeatable Read) - Khắc phục bằng REPEATABLE READ",
            "4. Khóa chết (Deadlock Msg 1205) - Khắc phục bằng Lock Ordering",
            "5. Đọc bóng ma (Phantom Read) - Khắc phục bằng SERIALIZABLE"
        ]
    )

    # Cấu hình mô tả nghiệp vụ cho 2 phiên làm việc
    if "1. Mất cập nhật" in selected_exp:
        s1_desc = "Xuất 15 cây Thép phi 10 tại KHO01. Đọc số tồn (465 cây), trễ kiểm kê thực địa 4.5s rồi ghi nhận tồn kho mới (450 cây)."
        s2_desc = "Nhập 50 cây Thép phi 10 vào KHO01. Gửi yêu cầu cập nhật sau 1.0s kể từ khi Phiên 1 bắt đầu."
        mode_options = [
            "Bản Lỗi (Không dùng khóa UPDLOCK - Mất dữ liệu)",
            "Bản Đã Xử Lý (Sử dụng WITH UPDLOCK - Toàn vẹn dữ liệu)"
        ]
    elif "2. Đọc dữ liệu rác" in selected_exp:
        s1_desc = "Cập nhật tạm thời số tồn KHO01 thành 999.00 cây (nhập nhầm), giữ Exclusive Lock 4.5s rồi hủy bỏ (ROLLBACK TRANSACTION)."
        s2_desc = "Đọc kiểm tra số tồn KHO01 tại thời điểm 1.0s để duyệt lệnh xuất kho."
        mode_options = [
            "Bản Lỗi (READ UNCOMMITTED - Đọc dữ liệu rác)",
            "Bản Đã Xử Lý (READ COMMITTED - Chặn đọc dữ liệu bẩn)"
        ]
    elif "3. Không đọc lại được" in selected_exp:
        s1_desc = "Lập báo cáo kiểm kê KHO01: Đọc số tồn lần 1 (t = 0s), trễ đối chiếu chứng từ 4.5s rồi đọc số tồn lần 2 (t = 4.5s) trong cùng giao tác."
        s2_desc = "Thực hiện nhập bổ sung 100 cây Thép phi 10 vào KHO01 tại thời điểm 1.0s và COMMIT ngay."
        mode_options = [
            "Bản Lỗi (READ COMMITTED - Dữ liệu biến thiên giữa 2 lần đọc)",
            "Bản Đã Xử Lý (REPEATABLE READ - Dữ liệu đọc giữ ổn định)"
        ]
    elif "4. Khóa chết" in selected_exp:
        s1_desc = "Điều chuyển 5 cây VT01 từ KHO01 sang KHO02. Bước 1: Khóa KHO01 (trừ 5), trễ xử lý 3.5s; Bước 2: Yêu cầu khóa KHO02 (cộng 5)."
        s2_desc = "Điều chuyển 2 cây VT01 từ KHO02 sang KHO01. Bước 1: Khóa KHO02 (trừ 2), trễ xử lý 3.5s; Bước 2: Yêu cầu khóa KHO01 (cộng 2)."
        mode_options = [
            "Bản Lỗi (Khóa chéo tài nguyên - Gây Deadlock Msg 1205)",
            "Bản Đã Xử Lý (Lock Ordering - Tuân thủ thứ tự khóa chuẩn)"
        ]
    else:
        s1_desc = "Tra cứu số lượng mặt hàng dưới mức tồn tối thiểu tại KHO02: Đọc lần 1 (t = 0s), trễ đối chiếu 4.5s rồi đọc lần 2 (t = 4.5s) trong cùng giao tác."
        s2_desc = "Thủ kho khác nhập bổ sung 1 mặt hàng mới (VT02 với số lượng tồn 15 bao <= định mức 100) vào KHO02 tại thời điểm 1.0s và COMMIT ngay."
        mode_options = [
            "Bản Lỗi (REPEATABLE READ - Xuất hiện bản ghi bóng ma)",
            "Bản Đã Xử Lý (SERIALIZABLE - Key-Range Lock chặn bóng ma)"
        ]

    col_cfg, col_act = st.columns([2, 1.2])
    with col_cfg:
        selected_mode = st.radio("Phiên bản thực thi:", mode_options, index=0)
    with col_act:
        st.write("")
        st.write("")
        btn_run = st.button("Chạy mô phỏng 2 người dùng song song", type="primary", use_container_width=True)

    # Khung giao diện 2 cột mô phỏng 2 người dùng song song
    col_s1, col_s2 = st.columns(2)

    with col_s1:
        st.markdown(f"""
        <div class="dual-user-container">
            <div class="dual-user-header">
                <div class="dual-user-title-s1">Phiên làm việc 1 - Nhân viên Kho chính (Session 1)</div>
                <span class="dual-user-role-badge-s1">Thủ kho KHO01</span>
            </div>
            <div class="dual-user-action-box">
                <b>Nghiệp vụ thực hiện:</b><br>{s1_desc}
            </div>
        </div>
        """, unsafe_allow_html=True)
        s1_status_box = st.empty()
        s1_status_box.markdown(render_status_badge("Sẵn sàng thực thi", "idle"), unsafe_allow_html=True)
        st.caption("Nhật ký giao dịch thời gian thực (Session 1):")
        s1_log_box = st.empty()
        s1_log_box.code("Nhấn 'Chạy mô phỏng' để bắt đầu phiên làm việc...", language="log")

    with col_s2:
        st.markdown(f"""
        <div class="dual-user-container">
            <div class="dual-user-header">
                <div class="dual-user-title-s2">Phiên làm việc 2 - Kế toán kho (Session 2)</div>
                <span class="dual-user-role-badge-s2">Kế toán kho</span>
            </div>
            <div class="dual-user-action-box-s2">
                <b>Nghiệp vụ thực hiện:</b><br>{s2_desc}
            </div>
        </div>
        """, unsafe_allow_html=True)
        s2_status_box = st.empty()
        s2_status_box.markdown(render_status_badge("Sẵn sàng thực thi", "idle"), unsafe_allow_html=True)
        st.caption("Nhật ký giao dịch thời gian thực (Session 2):")
        s2_log_box = st.empty()
        s2_log_box.code("Nhấn 'Chạy mô phỏng' để bắt đầu phiên làm việc...", language="log")

    # Xử lý khi nhấn nút Chạy mô phỏng
    if btn_run:
        chosen_mode = "error" if "Bản Lỗi" in selected_mode else "fixed"

        if "1. Mất cập nhật" in selected_exp:
            with st.spinner("Đang chạy mô phỏng 2 phiên giao tác đồng thời..."):
                final_stock = run_lost_update_dual(chosen_mode, s1_status_box, s1_log_box, s2_status_box, s2_log_box)

            st.write("---")
            st.markdown("##### Bảng đối chiếu biến động số dư trước và sau giao tác song song")
            diff = final_stock - 500.00
            eval_text = "AN TOÀN - UPDLOCK đã ngăn chặn ghi đè, số tồn chính xác." if final_stock == 500.00 else "NGHIÊM TRỌNG - Mất cập nhật (Lost Update), mất 50 cây nhập của Session 2!"
            
            df_comp = pd.DataFrame([
                {
                    "Chỉ tiêu đối chiếu": "Kho chính (KHO01) - Thép phi 10",
                    "Số dư ban đầu": format_quantity(465.0, "cây"),
                    "Số dư mong muốn": f"{format_quantity(500.0, 'cây')} (465 - 15 + 50)",
                    "Số dư thực tế trong CSDL sau khi chạy xong": format_quantity(final_stock, "cây"),
                    "Chênh lệch": format_quantity(diff, "cây", show_plus=True),
                    "Đánh giá an toàn giao tác": eval_text
                }
            ])
            st.dataframe(df_comp, use_container_width=True, hide_index=True)

            if chosen_mode == "error":
                st.error(f"Xác nhận lỗi Lost Update: Tồn kho thực tế dừng ở {format_quantity(final_stock, 'cây')} thay vì {format_quantity(500.0, 'cây')}. Giao tác của Session 2 bị Session 1 ghi đè hoàn toàn do không sử dụng khóa giữ chỗ (UPDLOCK).")
            else:
                st.success(f"Bảo toàn thành công: Tồn kho thực tế đạt {format_quantity(final_stock, 'cây')} chuẩn xác (465 - 15 + 50 = 500). Khóa WITH (UPDLOCK) đã bắt buộc Session 2 xếp hàng chờ Session 1 hoàn tất.")

        elif "2. Đọc dữ liệu rác" in selected_exp:
            with st.spinner("Đang chạy mô phỏng phiên cập nhật tạm và phiên đọc..."):
                s2_read_val, final_stock = run_dirty_read_dual(chosen_mode, s1_status_box, s1_log_box, s2_status_box, s2_log_box)

            st.write("---")
            st.markdown("##### Bảng đối chiếu biến động số dư trước và sau giao tác song song")
            diff_read = (s2_read_val - 465.00) if s2_read_val is not None else 0.0
            eval_read = "AN TOÀN - READ COMMITTED chặn đọc bẩn, chờ Rollback xong mới lấy số chuẩn." if s2_read_val == 465.00 else f"NGHIÊM TRỌNG - Đọc dữ liệu rác (Dirty Read {format_quantity(s2_read_val, 'cây')} chưa commit)!"
            
            df_comp = pd.DataFrame([
                {
                    "Chỉ tiêu đối chiếu": "Dữ liệu Kế toán kho (Session 2) đọc và ghi nhận",
                    "Số dư ban đầu": format_quantity(465.0, "cây"),
                    "Số dư mong muốn": f"{format_quantity(465.0, 'cây')} (Chỉ đọc dữ liệu đã COMMIT)",
                    "Số dư thực tế trong CSDL sau khi chạy xong": f"{format_quantity(s2_read_val, 'cây')} (Số liệu đọc)" if s2_read_val is not None else "N/A",
                    "Chênh lệch": format_quantity(diff_read, "cây", show_plus=True),
                    "Đánh giá an toàn giao tác": eval_read
                },
                {
                    "Chỉ tiêu đối chiếu": "Số dư tồn kho KHO01 thực tế trong CSDL",
                    "Số dư ban đầu": format_quantity(465.0, "cây"),
                    "Số dư mong muốn": f"{format_quantity(465.0, 'cây')} (Do Session 1 ROLLBACK)",
                    "Số dư thực tế trong CSDL sau khi chạy xong": format_quantity(final_stock, "cây"),
                    "Chênh lệch": format_quantity(0, "cây"),
                    "Đánh giá an toàn giao tác": "HỢP LỆ - CSDL đã Rollback hoàn toàn về giá trị ban đầu."
                }
            ])
            st.dataframe(df_comp, use_container_width=True, hide_index=True)

            if chosen_mode == "error":
                st.error(f"Xác nhận lỗi Dirty Read: Session 2 đọc phải giá trị rác {format_quantity(s2_read_val, 'cây')} trong khi thực tế Session 1 đã hủy (ROLLBACK). Mức cô lập READ UNCOMMITTED phá vỡ tính toàn vẹn dữ liệu kế toán.")
            else:
                st.success(f"Ngăn chặn thành công: Session 2 đã bị chặn đợi cho đến khi Session 1 ROLLBACK xong, sau đó đọc chính xác số dư hợp lệ {format_quantity(s2_read_val, 'cây')} dưới mức cô lập READ COMMITTED.")

        elif "3. Không đọc lại được" in selected_exp:
            with st.spinner("Đang chạy mô phỏng phiên đọc lặp lại và phiên cập nhật..."):
                r1, r2, final_stock = run_non_repeatable_read_dual(chosen_mode, s1_status_box, s1_log_box, s2_status_box, s2_log_box)

            st.write("---")
            st.markdown("##### Bảng đối chiếu biến động số dư trước và sau giao tác song song")
            r1_val = r1 if r1 is not None else 0.0
            r2_val = r2 if r2 is not None else 0.0
            diff_repeat = r2_val - r1_val
            eval_repeat = "AN TOÀN - REPEATABLE READ duy trì dữ liệu nhất quán trong suốt phiên làm việc." if r1_val == r2_val else "BẤT NHẤT - Không đọc lại được (Non-repeatable Read), số liệu nhảy vọt giữa 2 lần đọc!"
            
            df_comp = pd.DataFrame([
                {
                    "Chỉ tiêu đối chiếu": "Session 1 (Kho chính) - Đọc kiểm kê lần 1 (t = 0s)",
                    "Số dư ban đầu": format_quantity(465.0, "cây"),
                    "Số dư mong muốn": format_quantity(465.0, "cây"),
                    "Số dư thực tế trong CSDL sau khi chạy xong": format_quantity(r1_val, "cây"),
                    "Chênh lệch": format_quantity(0, "cây"),
                    "Đánh giá an toàn giao tác": "HỢP LỆ - Khởi tạo báo cáo kiểm kê."
                },
                {
                    "Chỉ tiêu đối chiếu": "Session 1 (Kho chính) - Đọc kiểm kê lần 2 (t = 4.5s)",
                    "Số dư ban đầu": format_quantity(465.0, "cây"),
                    "Số dư mong muốn": f"{format_quantity(465.0, 'cây')} (Đồng nhất dữ liệu trong 1 phiên)",
                    "Số dư thực tế trong CSDL sau khi chạy xong": format_quantity(r2_val, "cây"),
                    "Chênh lệch": format_quantity(diff_repeat, "cây", show_plus=True),
                    "Đánh giá an toàn giao tác": eval_repeat
                },
                {
                    "Chỉ tiêu đối chiếu": "Tồn kho KHO01 thực tế sau khi cả 2 phiên kết thúc",
                    "Số dư ban đầu": format_quantity(465.0, "cây"),
                    "Số dư mong muốn": f"{format_quantity(565.0, 'cây')} (Đã ghi nhận +100 cây của Session 2)",
                    "Số dư thực tế trong CSDL sau khi chạy xong": format_quantity(final_stock, "cây"),
                    "Chênh lệch": format_quantity(final_stock - 565.00, "cây", show_plus=True),
                    "Đánh giá an toàn giao tác": "HỢP LỆ - Giao tác nhập kho của Session 2 đã hoàn tất."
                }
            ])
            st.dataframe(df_comp, use_container_width=True, hide_index=True)

            if chosen_mode == "error":
                st.error(f"Xác nhận lỗi Non-repeatable Read: Session 1 đọc lần 1 được {format_quantity(r1_val, 'cây')}, nhưng lần 2 lại đọc ra {format_quantity(r2_val, 'cây')} trong cùng một giao tác. Báo cáo kiểm kê bị sai lệch do Session 2 chen ngang cập nhật.")
            else:
                st.success(f"Nhất quán tuyệt đối: Cả 2 lần đọc của Session 1 đều đạt {format_quantity(r1_val, 'cây')}. Mức cô lập REPEATABLE READ đã giữ Shared Lock, buộc Session 2 phải chờ Session 1 hoàn tất kiểm kê.")

        elif "4. Khóa chết" in selected_exp:
            with st.spinner("Đang chạy mô phỏng tranh chấp khóa chéo giữa 2 kho..."):
                results, final_k1, final_k2 = run_deadlock_dual(chosen_mode, s1_status_box, s1_log_box, s2_status_box, s2_log_box)

            st.write("---")
            st.markdown("##### Bảng đối chiếu biến động số dư trước và sau giao tác song song")
            diff_k1 = final_k1 - 462.00
            diff_k2 = final_k2 - 13.00
            eval_k1 = "AN TOÀN - Lock Ordering ngăn ngừa chu trình chờ, hoàn tất 100%." if chosen_mode == "fixed" else f"BỊ ẢNH HƯỞNG - {results.get('s1', '')}"
            eval_k2 = "AN TOÀN - Điều chuyển vật tư thành công." if chosen_mode == "fixed" else f"BỊ HỦY BỎ - {results.get('s2', '')}"
            
            df_comp = pd.DataFrame([
                {
                    "Chỉ tiêu đối chiếu": "Kho chính (KHO01) - Điều chuyển KHO01 -> KHO02",
                    "Số dư ban đầu": format_quantity(465.0, "cây"),
                    "Số dư mong muốn": f"{format_quantity(462.0, 'cây')} (465 - 5 + 2)",
                    "Số dư thực tế trong CSDL sau khi chạy xong": format_quantity(final_k1, "cây"),
                    "Chênh lệch": format_quantity(diff_k1, "cây", show_plus=True),
                    "Đánh giá an toàn giao tác": eval_k1
                },
                {
                    "Chỉ tiêu đối chiếu": "Kho phụ (KHO02) - Điều chuyển KHO02 -> KHO01",
                    "Số dư ban đầu": format_quantity(10.0, "cây"),
                    "Số dư mong muốn": f"{format_quantity(13.0, 'cây')} (10 + 5 - 2)",
                    "Số dư thực tế trong CSDL sau khi chạy xong": format_quantity(final_k2, "cây"),
                    "Chênh lệch": format_quantity(diff_k2, "cây", show_plus=True),
                    "Đánh giá an toàn giao tác": eval_k2
                }
            ])
            st.dataframe(df_comp, use_container_width=True, hide_index=True)

            if chosen_mode == "error":
                st.error(f"Xác nhận lỗi Deadlock (Msg 1205): SQL Server phát hiện chu trình khóa chéo (Cyclic Wait) giữa KHO01 và KHO02, tự động chọn 1 phiên làm Deadlock Victim và Rollback.\n- Kết quả Session 1: {results.get('s1', '')}\n- Kết quả Session 2: {results.get('s2', '')}")
            else:
                st.success(f"Giải quyết triệt để Deadlock: Cả 2 phiên đều hoàn thành và COMMIT thành công nhờ cơ chế Lock Ordering (luôn yêu cầu khóa KHO01 trước KHO02), triệt tiêu hoàn toàn khả năng hình thành chu trình chờ.")

        else:
            with st.spinner("Đang chạy mô phỏng đọc bóng ma và chèn bản ghi mới..."):
                r1, r2, final_cnt = run_phantom_read_dual(chosen_mode, s1_status_box, s1_log_box, s2_status_box, s2_log_box)

            st.write("---")
            st.markdown("##### Bảng đối chiếu biến động số lượng bản ghi thỏa điều kiện trước và sau giao tác")
            r1_val = r1 if r1 is not None else 0
            r2_val = r2 if r2 is not None else 0
            diff_phantom = r2_val - r1_val
            eval_phantom = "AN TOÀN - SERIALIZABLE khóa dải (Key-Range Lock), không có bản ghi bóng ma nào xuất hiện." if r1_val == r2_val else f"BẤT NHẤT - Xuất hiện bản ghi bóng ma (Phantom Read), tăng thêm {diff_phantom} mặt hàng giữa 2 lần đọc!"

            df_comp = pd.DataFrame([
                {
                    "Chỉ tiêu đối chiếu": "Session 1 (Kho phụ KHO02) - Đếm cảnh báo lần 1 (t = 0s)",
                    "Số dư ban đầu": "1 mặt hàng",
                    "Số dư mong muốn": "1 mặt hàng",
                    "Số dư thực tế trong CSDL sau khi chạy xong": f"{r1_val} mặt hàng",
                    "Chênh lệch": "0",
                    "Đánh giá an toàn giao tác": "HỢP LỆ - Phát hiện 1 mặt hàng chạm ngưỡng (VT01 tồn 10 <= định mức 50)."
                },
                {
                    "Chỉ tiêu đối chiếu": "Session 1 (Kho phụ KHO02) - Đếm cảnh báo lần 2 (t = 4.5s)",
                    "Số dư ban đầu": "1 mặt hàng",
                    "Số dư mong muốn": "1 mặt hàng (Đồng nhất số liệu trong 1 giao tác)",
                    "Số dư thực tế trong CSDL sau khi chạy xong": f"{r2_val} mặt hàng",
                    "Chênh lệch": f"{diff_phantom:+d} mặt hàng" if diff_phantom != 0 else "0",
                    "Đánh giá an toàn giao tác": eval_phantom
                },
                {
                    "Chỉ tiêu đối chiếu": "Trạng thái bảng TON_KHO sau khi cả 2 phiên kết thúc",
                    "Số dư ban đầu": "1 mặt hàng",
                    "Số dư mong muốn": "2 mặt hàng (Đã ghi nhận mặt hàng mới của Session 2)",
                    "Số dư thực tế trong CSDL sau khi chạy xong": f"{final_cnt} mặt hàng",
                    "Chênh lệch": "+1 mặt hàng",
                    "Đánh giá an toàn giao tác": "HỢP LỆ - Giao tác nhập mặt hàng mới của Session 2 hoàn tất an toàn."
                }
            ])
            st.dataframe(df_comp, use_container_width=True, hide_index=True)

            if chosen_mode == "error":
                st.error(f"Xác nhận lỗi Phantom Read: Session 1 đọc lần 1 đếm được {r1_val} mặt hàng, nhưng lần 2 lại đọc ra {r2_val} mặt hàng trong cùng giao tác. Mức cô lập REPEATABLE READ chỉ khóa các dòng hiện có, không ngăn được Session 2 chèn bản ghi mới (Phantom Record) thỏa điều kiện.")
            else:
                st.success(f"Khắc phục triệt để Phantom Read: Cả 2 lần đọc của Session 1 đều duy trì kết quả nhất quán {r1_val} mặt hàng. Mức cô lập SERIALIZABLE áp dụng khóa dải (Key-Range Lock), bắt buộc Session 2 phải chờ Session 1 hoàn tất giao tác.")
