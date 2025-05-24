import collections
import math
import matplotlib
matplotlib.use('Agg')  # Set backend for server environment
import matplotlib.pyplot as plt
import numpy as np
import base64
import io
import time
import traceback

# Set font để tránh warning
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']

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

# Hàm tạo biểu đồ phân tích entropy cho web API
def create_entropy_chart(result, mode='single', save_to_file=False):
    """
    Tạo biểu đồ phân tích entropy cho web API
    
    Args:
        result: Kết quả từ analyze_single_password hoặc analyze_password_file
        mode: 'single' hoặc 'file'
        save_to_file: True nếu muốn save file, False nếu return base64
    
    Returns:
        base64 string của hình ảnh hoặc file path
    """
    try:
        plt.style.use('default')
        
        if mode == 'single':
            # Single password entropy visualization
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12), facecolor='white')
            
            # 1. Entropy Comparison
            entropy_types = ['Shannon\nEntropy', 'Min-Entropy', 'Max Possible\nEntropy']
            entropy_values = [result['shannon_entropy'], result['min_entropy'], result['max_possible_entropy']]
            colors = ['#ff9500', '#ff3b30', '#34c759']
            
            bars1 = ax1.bar(entropy_types, entropy_values, color=colors, alpha=0.8, width=0.6)
            ax1.set_ylabel('Entropy (bits)', fontweight='bold')
            ax1.set_title(f'Entropy Analysis - "{result["password"][:20]}{"..." if len(result["password"]) > 20 else ""}"', 
                         fontweight='bold', pad=20)
            ax1.grid(True, alpha=0.3, axis='y')
            
            # Add values on bars
            for i, bar in enumerate(bars1):
                height = bar.get_height()
                ax1.annotate(f'{height:.2f}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom',
                            fontsize=12, fontweight='bold')
            
            # 2. Character Type Distribution
            char_types = ['Lowercase', 'Uppercase', 'Digits', 'Special']
            char_counts = [result['lowercase_count'], result['uppercase_count'], 
                          result['digit_count'], result['special_count']]
            colors2 = ['#007AFF', '#5856d6', '#34c759', '#ff9500']
            
            bars2 = ax2.bar(char_types, char_counts, color=colors2, alpha=0.8)
            ax2.set_ylabel('Count', fontweight='bold')
            ax2.set_title('Character Type Distribution', fontweight='bold', pad=20)
            ax2.tick_params(axis='x', rotation=45)
            ax2.grid(True, alpha=0.3, axis='y')
            
            # Add values on bars
            for bar in bars2:
                height = bar.get_height()
                ax2.annotate(f'{int(height)}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom',
                            fontsize=10, fontweight='bold')
            
            # 3. Entropy Ratio Gauge
            ratio = result['entropy_ratio']
            wedges, texts = ax3.pie([ratio, 100-ratio], 
                                   colors=['#ff9500', '#e5e5e7'],
                                   startangle=90,
                                   counterclock=False)
            
            # Add center circle for donut effect
            centre_circle = plt.Circle((0,0), 0.70, fc='white')
            ax3.add_artist(centre_circle)
            
            # Add ratio text in center
            ax3.text(0, 0, f'{ratio:.1f}%', 
                    horizontalalignment='center', verticalalignment='center',
                    fontsize=24, fontweight='bold', color='#ff9500')
            ax3.text(0, -0.3, 'Entropy Ratio', 
                    horizontalalignment='center', verticalalignment='center',
                    fontsize=12, fontweight='bold', color='#86868b')
            
            ax3.set_title('Entropy Efficiency', fontweight='bold', pad=20)
            
            # 4. Character Frequency (Top 8)
            if result['char_frequency'] and len(result['char_frequency']) > 0:
                top_chars = result['char_frequency'][:8]
                chars = [f"'{item['char']}'" for item in top_chars]
                frequencies = [item['frequency'] * 100 for item in top_chars]
                
                bars4 = ax4.bar(chars, frequencies, color='#5856d6', alpha=0.8)
                ax4.set_ylabel('Frequency (%)', fontweight='bold')
                ax4.set_title('Character Frequency Distribution (Top 8)', fontweight='bold', pad=20)
                ax4.tick_params(axis='x', rotation=45)
                ax4.grid(True, alpha=0.3, axis='y')
                
                # Add values on bars
                for bar in bars4:
                    height = bar.get_height()
                    ax4.annotate(f'{height:.1f}%',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom',
                                fontsize=9, fontweight='bold')
            else:
                ax4.text(0.5, 0.5, 'No character frequency data available', 
                        ha='center', va='center', transform=ax4.transAxes,
                        fontsize=14, color='#86868b')
                ax4.set_title('Character Frequency Distribution', fontweight='bold', pad=20)
        
        else:  # file mode
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12), facecolor='white')
            
            # 1. Entropy Statistics
            entropy_stats = ['Min Entropy', 'Avg Entropy', 'Max Entropy']
            entropy_vals = [result['min_entropy'], result['avg_entropy'], result['max_entropy']]
            colors = ['#ff3b30', '#ff9500', '#34c759']
            
            bars1 = ax1.bar(entropy_stats, entropy_vals, color=colors, alpha=0.8, width=0.6)
            ax1.set_ylabel('Entropy (bits)', fontweight='bold')
            ax1.set_title(f'Password Entropy Statistics\n({result["total_passwords"]} passwords)', 
                         fontweight='bold', pad=20)
            ax1.grid(True, alpha=0.3, axis='y')
            
            # Add values on bars
            for bar in bars1:
                height = bar.get_height()
                ax1.annotate(f'{height:.2f}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom',
                            fontsize=12, fontweight='bold')
            
            # 2. Character Distribution
            char_distribution = ['Shannon Entropy', 'Min-Entropy']
            char_dist_values = [result['char_distribution_entropy'], result['char_min_entropy']]
            colors2 = ['#007AFF', '#5856d6']
            
            bars2 = ax2.bar(char_distribution, char_dist_values, color=colors2, alpha=0.8)
            ax2.set_ylabel('Entropy (bits)', fontweight='bold')
            ax2.set_title('Character Distribution Entropy', fontweight='bold', pad=20)
            ax2.grid(True, alpha=0.3, axis='y')
            
            # Add values on bars
            for bar in bars2:
                height = bar.get_height()
                ax2.annotate(f'{height:.2f}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom',
                            fontsize=12, fontweight='bold')
            
            # 3. Character Type Distribution
            char_types = ['Lowercase', 'Uppercase', 'Digits', 'Special']
            char_counts = [result['lowercase_count'], result['uppercase_count'], 
                          result['digit_count'], result['special_count']]
            colors3 = ['#007AFF', '#5856d6', '#34c759', '#ff9500']
            
            bars3 = ax3.bar(char_types, char_counts, color=colors3, alpha=0.8)
            ax3.set_ylabel('Count', fontweight='bold')
            ax3.set_title('Character Type Distribution', fontweight='bold', pad=20)
            ax3.tick_params(axis='x', rotation=45)
            ax3.grid(True, alpha=0.3, axis='y')
            
            # Add values on bars
            for bar in bars3:
                height = bar.get_height()
                ax3.annotate(f'{int(height):,}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom',
                            fontsize=10, fontweight='bold')
            
            # 4. Top Characters Frequency
            if result['top_chars'] and len(result['top_chars']) > 0:
                top_chars = result['top_chars'][:8]
                chars = [f"'{item['char']}'" for item in top_chars]
                frequencies = [item['frequency'] * 100 for item in top_chars]
                
                bars4 = ax4.bar(chars, frequencies, color='#af52de', alpha=0.8)
                ax4.set_ylabel('Frequency (%)', fontweight='bold')
                ax4.set_title('Most Frequent Characters (Top 8)', fontweight='bold', pad=20)
                ax4.tick_params(axis='x', rotation=45)
                ax4.grid(True, alpha=0.3, axis='y')
                
                # Add values on bars
                for bar in bars4:
                    height = bar.get_height()
                    ax4.annotate(f'{height:.2f}%',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom',
                                fontsize=9, fontweight='bold')
            else:
                ax4.text(0.5, 0.5, 'No character frequency data available', 
                        ha='center', va='center', transform=ax4.transAxes,
                        fontsize=14, color='#86868b')
                ax4.set_title('Character Frequency Distribution', fontweight='bold', pad=20)
        
        # Overall title
        mode_text = "Single Password" if mode == 'single' else "File Analysis"
        fig.suptitle(f'Password Entropy Analysis Report - {mode_text}\nGenerated at: {time.strftime("%Y-%m-%d %H:%M:%S")}', 
                    fontsize=16, fontweight='bold', y=0.98)
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.92)
        
        if save_to_file:
            # Save to file
            chart_path = f"static/charts/entropy_{mode}_{int(time.time())}.png"
            import os
            os.makedirs(os.path.dirname(chart_path), exist_ok=True)
            plt.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            return chart_path
        else:
            # Return base64 string
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            buffer.close()
            return image_base64

            
    except Exception as e:
        print(f"Error creating entropy chart: {e}")
        traceback.print_exc()
        return None

def create_entropy_comparison_chart(results_list, labels, save_to_file=False):
    """
    Tạo biểu đồ so sánh entropy giữa nhiều file
    
    Args:
        results_list: List các kết quả entropy analysis
        labels: List tên các file
        save_to_file: True nếu muốn save file, False nếu return base64
    
    Returns:
        base64 string của hình ảnh hoặc file path
    """
    try:
        plt.style.use('default')
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12), facecolor='white')
        
        # Extract data
        avg_entropies = [r['avg_entropy'] for r in results_list]
        avg_lengths = [r['avg_length'] for r in results_list]
        char_entropies = [r['char_distribution_entropy'] for r in results_list]
        unique_chars = [r['unique_chars'] for r in results_list]
        
        x = np.arange(len(labels))
        
        # 1. Average Entropy Comparison
        bars1 = ax1.bar(x, avg_entropies, color='#ff9500', alpha=0.8)
        ax1.set_xlabel('Files', fontweight='bold')
        ax1.set_ylabel('Average Entropy (bits)', fontweight='bold')
        ax1.set_title('Average Password Entropy Comparison', fontweight='bold', pad=20)
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels, rotation=45, ha='right')
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Add values on bars
        for bar in bars1:
            height = bar.get_height()
            ax1.annotate(f'{height:.2f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=10, fontweight='bold')
        
        # 2. Average Length Comparison
        bars2 = ax2.bar(x, avg_lengths, color='#007AFF', alpha=0.8)
        ax2.set_xlabel('Files', fontweight='bold')
        ax2.set_ylabel('Average Length (characters)', fontweight='bold')
        ax2.set_title('Average Password Length Comparison', fontweight='bold', pad=20)
        ax2.set_xticks(x)
        ax2.set_xticklabels(labels, rotation=45, ha='right')
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Add values on bars
        for bar in bars2:
            height = bar.get_height()
            ax2.annotate(f'{height:.2f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=10, fontweight='bold')
        
        # 3. Character Distribution Entropy
        bars3 = ax3.bar(x, char_entropies, color='#34c759', alpha=0.8)
        ax3.set_xlabel('Files', fontweight='bold')
        ax3.set_ylabel('Character Distribution Entropy (bits)', fontweight='bold')
        ax3.set_title('Character Distribution Entropy Comparison', fontweight='bold', pad=20)
        ax3.set_xticks(x)
        ax3.set_xticklabels(labels, rotation=45, ha='right')
        ax3.grid(True, alpha=0.3, axis='y')
        
        # Add values on bars
        for bar in bars3:
            height = bar.get_height()
            ax3.annotate(f'{height:.2f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=10, fontweight='bold')
        
        # 4. Unique Characters Comparison
        bars4 = ax4.bar(x, unique_chars, color='#5856d6', alpha=0.8)
        ax4.set_xlabel('Files', fontweight='bold')
        ax4.set_ylabel('Unique Characters', fontweight='bold')
        ax4.set_title('Character Diversity Comparison', fontweight='bold', pad=20)
        ax4.set_xticks(x)
        ax4.set_xticklabels(labels, rotation=45, ha='right')
        ax4.grid(True, alpha=0.3, axis='y')
        
        # Add values on bars
        for bar in bars4:
            height = bar.get_height()
            ax4.annotate(f'{int(height)}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=10, fontweight='bold')
        
        fig.suptitle(f'Entropy Analysis Comparison Report\nGenerated at: {time.strftime("%Y-%m-%d %H:%M:%S")}', 
                    fontsize=16, fontweight='bold', y=0.98)
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.92)
        
        if save_to_file:
            chart_path = f"static/charts/entropy_comparison_{int(time.time())}.png"
            import os
            os.makedirs(os.path.dirname(chart_path), exist_ok=True)
            plt.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            return chart_path
        else:
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            buffer.close()
            return image_base64
                
    except Exception as e:
        print(f"Error creating entropy comparison chart: {e}")
        traceback.print_exc()
        return None