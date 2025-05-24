import collections
import math

# Hàm làm sạch dữ liệu mật khẩu
def cleanup_data(input_file, output_file=None):
    processed_passwords = []
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

    except FileNotFoundError:
        print(f"Không tìm thấy tệp: {input_file}")
        return

    except Exception as e:
        print(f"Lỗi: {e}")
        return

    for line in lines:
        line = line.strip()
        if not line:
            continue

        parts = line.split(' ', 1)
        if len(parts) > 1:
            password = parts[1]
            processed_passwords.append(password)
        else:
            processed_passwords.append('')
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            for password in processed_passwords:
                f.write(password + '\n')
        print(f"Đã ghi vào tệp: {output_file}")

    else:
        for password in processed_passwords:
            print(password)

# Hàm phân tích mật khẩu đơn cho web API
def analyze_single_password(password):
    """
    Phân tích entropy cho một mật khẩu đơn
    
    Args:
        password (str): Mật khẩu cần phân tích
    
    Returns:
        dict: Kết quả phân tích entropy
    """
    R = 95  # ASCII printable characters
    length = len(password)
    
    if length == 0:
        return {
            'error': 'Password is empty'
        }
    
    # Character distribution analysis
    char_count = collections.Counter(password)
    unique_chars = len(char_count)
    
    # Shannon entropy
    shannon_entropy = 0.0
    for count in char_count.values():
        p = count / length
        shannon_entropy -= p * math.log2(p)
    
    # Min-entropy (based on most frequent character)
    max_p = max(char_count.values()) / length if char_count.values() else 0
    min_entropy = -math.log2(max_p) if max_p > 0 else 0
    
    # Max possible entropy
    max_possible_entropy = math.log2(min(R, length)) if length > 0 else 0
    
    # Entropy ratio
    entropy_ratio = (shannon_entropy / max_possible_entropy * 100) if max_possible_entropy > 0 else 0
    
    # Character type counts
    lowercase_count = sum(1 for c in password if c.islower())
    uppercase_count = sum(1 for c in password if c.isupper())
    digit_count = sum(1 for c in password if c.isdigit())
    special_count = length - lowercase_count - uppercase_count - digit_count
    
    # Character frequency analysis
    char_frequency = [
        {
            'char': char,
            'count': count,
            'frequency': count / length
        }
        for char, count in char_count.most_common()
    ]
    
    return {
        'password': password,
        'length': length,
        'shannon_entropy': shannon_entropy,
        'min_entropy': min_entropy,
        'max_possible_entropy': max_possible_entropy,
        'entropy_ratio': entropy_ratio,
        'unique_chars': unique_chars,
        'lowercase_count': lowercase_count,
        'uppercase_count': uppercase_count,
        'digit_count': digit_count,
        'special_count': special_count,
        'char_frequency': char_frequency
    }

# Hàm phân tích file mật khẩu cho web API
def analyze_password_file(file_path):
    """
    Phân tích entropy cho file mật khẩu
    
    Args:
        file_path (str): Đường dẫn đến file mật khẩu
    
    Returns:
        dict: Kết quả phân tích entropy
    """
    try:
        R = 95  # 95 ký tự ASCII có thể in được
        
        with open(file_path, 'r', encoding='utf-8') as f:
            passwords = [line.strip() for line in f if line.strip()]
        
        num_passwords = len(passwords)
        if num_passwords == 0:
            return {'error': 'No valid passwords found in file'}
        
        entropies = []
        total_length = 0
        for p in passwords:
            L = len(p)
            total_length += L
            E = L * math.log2(R)  # Shannon entropy
            entropies.append(E)
        
        min_E = min(entropies) if entropies else 0
        max_E = max(entropies) if entropies else 0
        mean_E = sum(entropies) / num_passwords if num_passwords > 0 else 0
        avg_length = total_length / num_passwords if num_passwords > 0 else 0
        
        # Tính phân phối ký tự
        all_chars = ''.join(passwords)
        N = len(all_chars)
        char_count = collections.Counter(all_chars)
        unique_chars = len(char_count)
        
        # Tính Shannon entropy của phân phối ký tự
        H_char = 0.0
        for count in char_count.values():
            p = count / N
            if p > 0:
                H_char -= p * math.log2(p)
        
        # Tính min-entropy của phân phối ký tự
        max_p = max(char_count.values(), default=0) / N
        H_min_char = -math.log2(max_p) if max_p > 0 else 0
        
        # Đếm các loại ký tự
        lowercase_count = sum(1 for c in all_chars if c.islower())
        uppercase_count = sum(1 for c in all_chars if c.isupper())
        digit_count = sum(1 for c in all_chars if c.isdigit())
        special_count = N - lowercase_count - uppercase_count - digit_count
        
        # Top characters
        top_chars = [
            {
                'char': char,
                'count': count,
                'frequency': count / N
            }
            for char, count in char_count.most_common(10)
        ]
        
        return {
            'total_passwords': num_passwords,
            'avg_length': avg_length,
            'min_entropy': min_E,
            'max_entropy': max_E,
            'avg_entropy': mean_E,
            'total_chars': N,
            'unique_chars': unique_chars,
            'char_distribution_entropy': H_char,
            'char_min_entropy': H_min_char,
            'lowercase_count': lowercase_count,
            'uppercase_count': uppercase_count,
            'digit_count': digit_count,
            'special_count': special_count,
            'top_chars': top_chars
        }
    
    except Exception as e:
        return {'error': str(e)}

# Hàm phân tích mật khẩu gốc
def password_analysis(filename):
    R = 95  # 95 ký tự ASCII có thể in được

    with open(filename, 'r', encoding='utf-8') as file:
        passwords = [line.strip() for line in file]

    num_passwords = len(passwords)
    if num_passwords == 0:
        print("Danh sách mật khẩu trống.")
        return

    entropies = []
    total_length = 0
    for p in passwords:
        L = len(p)
        total_length += L
        E = L * math.log2(R)  # Shannon entropy
        entropies.append(E)

    min_E = min(entropies) if entropies else 0  # Entropy tối thiểu
    max_E = max(entropies) if entropies else 0  # Entropy tối đa
    mean_E = sum(entropies) / num_passwords if num_passwords > 0 else 0  # Entropy trung bình
    avg_length = total_length / num_passwords if num_passwords > 0 else 0  # Độ dài trung bình

    # Tính phân phối ký tự
    all_chars = ''.join(passwords)
    N = len(all_chars)
    char_count = collections.Counter(all_chars)
    unique_chars = len(char_count)

    # Tính Shannon entropy của phân phối ký tự
    H_char = 0.0
    for count in char_count.values():
        p = count / N
        if p > 0:
            H_char -= p * math.log2(p)

    # Tính min-entropy của phân phối ký tự
    max_p = max(char_count.values(), default=0) / N
    H_min_char = -math.log2(max_p) if max_p > 0 else 0

    # Đếm các loại ký tự
    lowercase_count = sum(1 for c in all_chars if c.islower())
    uppercase_count = sum(1 for c in all_chars if c.isupper())
    digit_count = sum(1 for c in all_chars if c.isdigit())
    special_count = N - lowercase_count - uppercase_count - digit_count

    print(f"*** Phân tích mật khẩu | {filename} ***")
    print(f"Tổng số mật khẩu: {num_passwords}")
    print(f"Độ dài mật khẩu trung bình: {avg_length:.2f}")
    print(f"Entropy tối thiểu: {min_E:.2f} bits")
    print(f"Entropy tối đa: {max_E:.2f} bits")
    print(f"Entropy trung bình: {mean_E:.2f} bits")

    print(f"Tổng số ký tự: {N}")
    print(f"Tổng số ký tự duy nhất: {unique_chars}")
    print(f"Shannon entropy của phân phối mật khẩu: {H_char:.2f} bits")
    print(f"Min-entropy của phân phối mật khẩu: {H_min_char:.2f} bits")
    print(f"Ký tự thường: {lowercase_count}")
    print(f"Ký tự hoa: {uppercase_count}")
    print(f"Chữ số: {digit_count}")
    print(f"Ký tự đặc biệt: {special_count}")

    # Top 5 ký tự phổ biến nhất
    top5 = char_count.most_common(5)
    print("Top 5 ký tự phổ biến:")
    for char, count in top5:
        print(f"{char}: {count} ({count/N:.4f})")

# Phần chạy script gốc (chỉ chạy khi file được chạy trực tiếp)
if __name__ == "__main__":
    # Làm sạch tệp mật khẩu đầu vào và lưu ra tệp đích
    cleanup_data('Normal-GEN-raw.txt', 'Normal-GEN.txt')

    # Danh sách các tệp mật khẩu cần phân tích
    files = ['Normal-GEN.txt', 'DC-GEN-[cuda_0]-last.txt', 'PassGPT-GEN.txt']
    for file in files:
        password_analysis(file)
        print()
