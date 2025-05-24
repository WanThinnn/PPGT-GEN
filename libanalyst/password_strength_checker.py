import re
from typing import Tuple, List
from multiprocessing import Pool, cpu_count
from itertools import chain
import mmap
from datetime import datetime
import os
from collections import Counter

# Biên dịch trước các biểu thức chính quy
PATTERNS = {
    'uppercase': re.compile(r'[A-Z]'),
    'lowercase': re.compile(r'[a-z]'),
    'digit': re.compile(r'\d'),
    'special': re.compile(r'[!@#$%^&*(),.?":{}|<>]')
}

def check_single_password(password: str) -> Tuple[bool, List[str]]:
    """
    Kiểm tra độ mạnh của một mật khẩu.
    """
    issues = []
    
    if len(password) < 8:
        issues.append("Mật khẩu quá ngắn (cần ít nhất 8 ký tự)")
    if not PATTERNS['uppercase'].search(password):
        issues.append("Thiếu chữ hoa")
    if not PATTERNS['lowercase'].search(password):
        issues.append("Thiếu chữ thường")
    if not PATTERNS['digit'].search(password):
        issues.append("Thiếu số")
    if not PATTERNS['special'].search(password):
        issues.append("Thiếu ký tự đặc biệt")
    
    return len(issues) == 0, issues

def process_password_chunk(args: Tuple[int, str]) -> Tuple[int, str, bool, List[str]]:
    """
    Xử lý một mật khẩu và trả về kết quả cùng với index.
    """
    index, password = args
    password = password.strip()
    if not password:
        return index, "", False, []
    
    is_strong, issues = check_single_password(password)
    return index, password, is_strong, issues

def save_results_to_file(
    filename: str,
    total_passwords: int,
    strong_passwords: int,
    weak_passwords: int,
    issue_counter: Counter
) -> None:
    """
    Lưu kết quả thống kê tổng hợp vào file txt, bao gồm thống kê chi tiết các vấn đề.
    """
    if not os.path.exists('results'):
        os.makedirs('results')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stats_filename = f'results/password_stats_{timestamp}.txt'
    with open(stats_filename, 'w', encoding='utf-8') as f:
        f.write(f"BÁO CÁO PHÂN TÍCH MẬT KHẨU\n")
        f.write(f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"File nguồn: {filename}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Tổng số mật khẩu: {total_passwords}\n")
        f.write(f"Mật khẩu mạnh: {strong_passwords} ({strong_passwords/total_passwords*100:.1f}%)\n")
        f.write(f"Mật khẩu yếu: {weak_passwords} ({weak_passwords/total_passwords*100:.1f}%)\n\n")
        f.write("Thống kê chi tiết các vấn đề ở mật khẩu yếu:\n")
        if issue_counter:
            for issue, count in issue_counter.most_common():
                f.write(f"  - {issue}: {count} lần\n")
        else:
            f.write("  Không có vấn đề nào được ghi nhận.\n")
    print(f"\nĐã lưu kết quả thống kê vào file: {stats_filename}")

def analyze_password_file(filename: str) -> None:
    """
    Phân tích file mật khẩu sử dụng đa luồng.
    """
    try:
        # Đọc file sử dụng memory mapping để tối ưu bộ nhớ
        with open(filename, 'r', encoding='utf-8') as file:
            # Sử dụng mmap để đọc file hiệu quả hơn
            with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                # Đọc toàn bộ nội dung và chia thành các dòng
                content = mm.read().decode('utf-8')
                passwords = content.splitlines()
        
        total_passwords = len(passwords)
        if total_passwords == 0:
            print("File trống!")
            return

        # Tạo pool process với số lượng process bằng số CPU
        num_processes = max(1, 14)  # Để lại 1 CPU cho hệ thống
        print(f"\nSử dụng {num_processes} process để xử lý...")
        
        # Tạo danh sách các cặp (index, password) để xử lý
        password_args = list(enumerate(passwords, 1))
        
        # Xử lý song song các mật khẩu
        with Pool(processes=num_processes) as pool:
            results = pool.map(process_password_chunk, password_args)
        
        # Sắp xếp kết quả theo index
        results.sort(key=lambda x: x[0])
        
        # Thống kê kết quả
        strong_passwords = sum(1 for _, _, is_strong, _ in results if is_strong)
        weak_passwords = total_passwords - strong_passwords
        
        # In kết quả ra màn hình
        print(f"\nPhân tích {total_passwords} mật khẩu từ file {filename}")
        print("-" * 50)
        
        # In kết quả
        for index, password, is_strong, issues in results:
            if not password:  # Bỏ qua dòng trống
                continue
                
            if is_strong:
                print(f"\nMật khẩu #{index}: {password}")
                print("✓ Mật khẩu mạnh")
            else:
                print(f"\nMật khẩu #{index}: {password}")
                print("✗ Mật khẩu yếu")
                print("Các vấn đề:")
                for issue in issues:
                    print(f"  - {issue}")
        
        print("\n" + "=" * 50)
        print(f"Tổng số mật khẩu: {total_passwords}")
        print(f"Mật khẩu mạnh: {strong_passwords} ({strong_passwords/total_passwords*100:.1f}%)")
        print(f"Mật khẩu yếu: {weak_passwords} ({weak_passwords/total_passwords*100:.1f}%)")
        
        # Lưu kết quả vào file (chỉ lưu thống kê)
        issue_counter = Counter()
        for _, _, is_strong, issues in results:
            if not is_strong:
                issue_counter.update(issues)
        
        save_results_to_file(filename, total_passwords, strong_passwords, weak_passwords, issue_counter)
        
    except FileNotFoundError:
        print(f"Không tìm thấy file {filename}")
    except Exception as e:
        print(f"Có lỗi xảy ra: {str(e)}")

if __name__ == "__main__":
    filename = "PassGPT-GEN.txt"
    analyze_password_file(filename)