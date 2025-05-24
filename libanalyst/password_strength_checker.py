import re
from typing import Tuple, List, Dict, Any
from multiprocessing import Pool, cpu_count
from itertools import chain
import mmap
from datetime import datetime
import os
from collections import Counter
import matplotlib
matplotlib.use('Agg')  # Set backend for server environment
import matplotlib.pyplot as plt
import numpy as np
import base64
import io
import time
import traceback
from libanalyst import password_strength_checker

# Set font để tránh warning
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']

# Biên dịch trước các biểu thức chính quy
PATTERNS = {
    'uppercase': re.compile(r'[A-Z]'),
    'lowercase': re.compile(r'[a-z]'),
    'digit': re.compile(r'\d'),
    'special': re.compile(r'[!@#$%^&*(),.?":{}|<>]')
}

def check_single_password(password: str) -> Tuple[bool, List[str]]:
    """
    Kiểm tra độ mạnh của một mật khẩu đơn
    
    Args:
        password: Mật khẩu cần kiểm tra
        
    Returns:
        Tuple[is_strong, list_of_issues]
    """
    issues = []
    
    # Kiểm tra độ dài
    if len(password) < 8:
        issues.append("Mật khẩu quá ngắn (cần ít nhất 8 ký tự)")
    
    # Kiểm tra có chữ hoa
    if not PATTERNS['uppercase'].search(password):
        issues.append("Thiếu ký tự hoa (A-Z)")
    
    # Kiểm tra có chữ thường
    if not PATTERNS['lowercase'].search(password):
        issues.append("Thiếu ký tự thường (a-z)")
    
    # Kiểm tra có số
    if not PATTERNS['digit'].search(password):
        issues.append("Thiếu số (0-9)")
    
    # Kiểm tra có ký tự đặc biệt
    if not PATTERNS['special'].search(password):
        issues.append("Thiếu ký tự đặc biệt (!@#$%^&*...)")
    
    # Kiểm tra các pattern phổ biến
    if password.lower() in ['password', '123456', 'qwerty', 'admin']:
        issues.append("Mật khẩu quá phổ biến")
    
    # Mật khẩu mạnh khi không có vấn đề nào
    is_strong = len(issues) == 0
    
    return is_strong, issues

def process_password_chunk(args: Tuple[int, str]) -> Tuple[int, str, bool, List[str]]:
    """
    Xử lý một mật khẩu trong multiprocessing
    """
    index, password = args
    is_strong, issues = check_single_password(password)
    return index, password, is_strong, issues

def analyze_multiple_files_for_comparison(file_paths: List[str], model_names: List[str]) -> Dict[str, Any]:
    """
    Phân tích nhiều file để so sánh mật khẩu mạnh giữa các model
    """
    try:
        results = {}
        comparison_data = []
        
        for i, (file_path, model_name) in enumerate(zip(file_paths, model_names)):
            # Đọc và phân tích từng file
            with open(file_path, 'r', encoding='utf-8') as file:
                passwords = [line.strip() for line in file if line.strip()]
            
            total_passwords = len(passwords)
            if total_passwords == 0:
                continue
            
            # Phân tích từng mật khẩu
            num_processes = max(1, min(8, cpu_count() - 1))
            password_args = list(enumerate(passwords, 1))
            
            with Pool(processes=num_processes) as pool:
                analysis_results = pool.map(process_password_chunk, password_args)
            
            # Thống kê kết quả
            strong_passwords = [r for r in analysis_results if r[2]]  # is_strong = True
            weak_passwords = [r for r in analysis_results if not r[2]]
            
            strong_count = len(strong_passwords)
            weak_count = len(weak_passwords)
            strong_percentage = (strong_count / total_passwords) * 100
            
            # Thống kê các vấn đề
            issue_counter = Counter()
            for _, _, is_strong, issues in analysis_results:
                if not is_strong:
                    issue_counter.update(issues)
            
            # Phân tích độ dài mật khẩu
            strong_lengths = [len(r[1]) for r in strong_passwords]
            weak_lengths = [len(r[1]) for r in weak_passwords]
            
            avg_strong_length = np.mean(strong_lengths) if strong_lengths else 0
            avg_weak_length = np.mean(weak_lengths) if weak_lengths else 0
            avg_total_length = np.mean([len(p) for p in passwords])
            
            # Phân tích ký tự
            strong_char_stats = analyze_character_distribution([r[1] for r in strong_passwords])
            weak_char_stats = analyze_character_distribution([r[1] for r in weak_passwords])
            
            model_result = {
                'model_name': model_name,
                'file_path': file_path,
                'total_passwords': total_passwords,
                'strong_count': strong_count,
                'weak_count': weak_count,
                'strong_percentage': round(strong_percentage, 2),
                'weak_percentage': round(100 - strong_percentage, 2),
                'avg_strong_length': round(avg_strong_length, 2),
                'avg_weak_length': round(avg_weak_length, 2),
                'avg_total_length': round(avg_total_length, 2),
                'strong_passwords': [r[1] for r in strong_passwords[:50]],  # Top 50 for preview
                'common_issues': [{'issue': issue, 'count': count} for issue, count in issue_counter.most_common(10)],
                'strong_char_stats': strong_char_stats,
                'weak_char_stats': weak_char_stats
            }
            
            results[model_name] = model_result
            comparison_data.append(model_result)
        
        # Tính toán ranking
        comparison_data.sort(key=lambda x: x['strong_percentage'], reverse=True)
        for i, model in enumerate(comparison_data):
            model['rank'] = i + 1
        
        # Tổng hợp so sánh
        comparison_summary = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_models': len(comparison_data),
            'models': comparison_data,
            'individual_results': results,
            'best_model': comparison_data[0] if comparison_data else None,
            'worst_model': comparison_data[-1] if comparison_data else None,
        }
        
        return comparison_summary
        
    except Exception as e:
        return {'error': f'Error analyzing files: {str(e)}'}

def analyze_character_distribution(passwords: List[str]) -> Dict[str, Any]:
    """
    Phân tích phân phối ký tự trong danh sách mật khẩu
    """
    if not passwords:
        return {
            'avg_uppercase': 0,
            'avg_lowercase': 0,
            'avg_digits': 0,
            'avg_special': 0,
            'total_chars': 0,
            'unique_chars': 0
        }
    
    total_uppercase = 0
    total_lowercase = 0
    total_digits = 0
    total_special = 0
    all_chars = set()
    
    for password in passwords:
        total_uppercase += len(PATTERNS['uppercase'].findall(password))
        total_lowercase += len(PATTERNS['lowercase'].findall(password))
        total_digits += len(PATTERNS['digit'].findall(password))
        total_special += len(PATTERNS['special'].findall(password))
        all_chars.update(password)
    
    count = len(passwords)
    return {
        'avg_uppercase': round(total_uppercase / count, 2),
        'avg_lowercase': round(total_lowercase / count, 2),
        'avg_digits': round(total_digits / count, 2),
        'avg_special': round(total_special / count, 2),
        'total_chars': len(''.join(passwords)),
        'unique_chars': len(all_chars)
    }

def create_strength_comparison_chart(comparison_data: Dict[str, Any], save_to_file=False):
    """
    Tạo biểu đồ so sánh strength giữa các model
    """
    try:
        plt.style.use('default')
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12), facecolor='white')
        
        models = comparison_data['models']
        model_names = [m['model_name'] for m in models]
        
        # 1. Strong Password Percentage Comparison
        strong_percentages = [m['strong_percentage'] for m in models]
        colors1 = ['#34c759', '#ff9500', '#5856d6', '#ff3b30'][:len(models)]
        
        bars1 = ax1.bar(model_names, strong_percentages, color=colors1, alpha=0.8)
        ax1.set_ylabel('Strong Password Percentage (%)', fontweight='bold')
        ax1.set_title('Strong Password Percentage by Model', fontweight='bold', pad=20)
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3, axis='y')
        ax1.set_ylim(0, 100)
        
        # Add values on bars
        for bar in bars1:
            height = bar.get_height()
            ax1.annotate(f'{height:.1f}%',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=12, fontweight='bold')
        
        # 2. Total Passwords Count
        total_counts = [m['total_passwords'] for m in models]
        colors2 = ['#007AFF', '#ff6b47', '#af52de', '#32cd32'][:len(models)]
        
        bars2 = ax2.bar(model_names, total_counts, color=colors2, alpha=0.8)
        ax2.set_ylabel('Total Passwords', fontweight='bold')
        ax2.set_title('Total Password Count by Model', fontweight='bold', pad=20)
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Add values on bars
        for bar in bars2:
            height = bar.get_height()
            ax2.annotate(f'{int(height):,}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=10, fontweight='bold')
        
        # 3. Average Password Length Comparison
        avg_lengths = [m['avg_total_length'] for m in models]
        strong_lengths = [m['avg_strong_length'] for m in models]
        
        x = np.arange(len(model_names))
        width = 0.35
        
        bars3a = ax3.bar(x - width/2, avg_lengths, width, label='Average Length', color='#5856d6', alpha=0.7)
        bars3b = ax3.bar(x + width/2, strong_lengths, width, label='Strong Password Length', color='#34c759', alpha=0.7)
        
        ax3.set_ylabel('Average Length (characters)', fontweight='bold')
        ax3.set_title('Password Length Comparison', fontweight='bold', pad=20)
        ax3.set_xticks(x)
        ax3.set_xticklabels(model_names, rotation=45)
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')
        
        # Add values on bars
        for bars in [bars3a, bars3b]:
            for bar in bars:
                height = bar.get_height()
                ax3.annotate(f'{height:.1f}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom',
                            fontsize=9, fontweight='bold')
        
        # 4. Character Distribution Comparison
        char_types = ['Uppercase', 'Lowercase', 'Digits', 'Special']
        x_chars = np.arange(len(char_types))
        bar_width = 0.2
        
        for i, model in enumerate(models[:4]):  # Max 4 models for readability
            char_values = [
                model['strong_char_stats']['avg_uppercase'],
                model['strong_char_stats']['avg_lowercase'],
                model['strong_char_stats']['avg_digits'],
                model['strong_char_stats']['avg_special']
            ]
            
            ax4.bar(x_chars + i * bar_width, char_values, bar_width, 
                   label=model['model_name'], alpha=0.8,
                   color=colors1[i] if i < len(colors1) else f'C{i}')
        
        ax4.set_ylabel('Average Count per Password', fontweight='bold')
        ax4.set_title('Character Distribution in Strong Passwords', fontweight='bold', pad=20)
        ax4.set_xticks(x_chars + bar_width * 1.5)
        ax4.set_xticklabels(char_types)
        ax4.legend()
        ax4.grid(True, alpha=0.3, axis='y')
        
        # Overall title
        fig.suptitle(f'Password Strength Comparison Report\nGenerated at: {comparison_data["timestamp"]}', 
                    fontsize=16, fontweight='bold', y=0.98)
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.92)
        
        if save_to_file:
            chart_path = f"static/charts/strength_comparison_{int(time.time())}.png"
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
        print(f"Error creating strength comparison chart: {e}")
        traceback.print_exc()
        return None

# if __name__ == "__main__":
#     filename = "PassGPT-GEN.txt"
#     analyze_password_file(filename)