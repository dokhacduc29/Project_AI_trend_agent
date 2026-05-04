import csv
import os
import logging
from collections import defaultdict

def save_to_csv(data_list, filename):
    """
    Hàm lưu dữ liệu xuống file CSV và ứng dụng DefaultDict để thông kê.
    Quy tắc L02: Đổi TOÀN BỘ lệnh print() sang logging.
    """
    existing_titles = set() 
    file_exists = os.path.isfile(filename)
    
    # 1. Đọc lịch sử để chống trùng lặp (Set Comprehension O(N))
    if file_exists:
        try:
            with open(filename, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                existing_titles = {row["Tieu_De"].strip() for row in reader if "Tieu_De" in row} 
        except Exception as e:
            logging.error(f"Lỗi khi đọc file cũ: {e}")

    # 2. Lọc tin thực sự mới (NamedTuple object)
    new_data = [art for art in data_list if art.title.strip() not in existing_titles]
    
    if not new_data:
        logging.info("Quét xong! Không có tin mới nào. Dữ liệu cũ được GIỮ NGUYÊN an toàn.")
        return False

    # =====================================================================
    # [DAY 14] GOM NHÓM (GROUP BY) THÔNG MINH VỚI DEFAULTDICT
    # =====================================================================
    # Nếu dùng Dictionary thường: Bạn phải if-else kiểm tra xem key tồn tại chưa.
    # Với defaultdict(int): Khởi tạo mặc định số 0. Code sạch gấp 10 lần.
    source_stats = defaultdict(int)
    tag_stats = defaultdict(int)
    
    for art in new_data:
        source_stats[art.source] += 1
        for tag in art.tags:
            tag_stats[tag] += 1
            
    logging.info("📊 Thống kê nguồn tin mới thu thập:")
    for source, count in source_stats.items():
        logging.info(f"   [Nguồn] {source}: {count} bài")
        
    for tag, count in tag_stats.items():
        logging.info(f"   [Tag] {tag}: Xuất hiện {count} lần")

    # 3. Ghi nối tiếp (Append-only) tin mới
    try:
        with open(filename, mode='a', encoding='utf-8', newline='') as f:
            fieldnames = ["STT", "Tieu_De", "Nguon", "Ngay", "Mieu_Ta", "Noi_Dung", "Link_Anh", "Link_Bai"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
                
            start_idx = len(existing_titles) + 1
            
            for i, art in enumerate(new_data, start_idx):
                writer.writerow({
                    "STT": i,
                    "Tieu_De": art.title,
                    "Nguon": art.source,
                    "Ngay": art.date,
                    "Mieu_Ta": ", ".join(art.tags), # Lưu Tags bằng dấu phẩy
                    "Noi_Dung": "",
                    "Link_Anh": "",
                    "Link_Bai": art.url
                })
        logging.info(f"Đã nối thêm {len(new_data)} tin MỚI vào: {filename}")
        return True
        
    except Exception as e:
        logging.error(f"Lỗi ghi file CSV: {e}")
        return False