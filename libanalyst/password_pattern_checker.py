import argparse, math, itertools
from collections import Counter
import matplotlib
matplotlib.use('Agg')  # Set backend for server environment
import matplotlib.pyplot as plt
import numpy as np
import base64
import io
import os
import time
import traceback

# Set font để tránh warning
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']

def load_passwords(path):
    with open(path, encoding='utf-8', errors='ignore') as f:
        return [l.strip() for l in f if l.strip()]


def get_pattern(pw):
    pat = []
    for c in pw:
        if c.islower():   pat.append('L')
        elif c.isupper(): pat.append('U')
        elif c.isdigit(): pat.append('D')
        else:             pat.append('S')
    return ''.join(pat)


def normalize(counter):
    total = sum(counter.values())
    return {k: v / total for k, v in counter.items()}


def length_dist(pws):
    cnt = Counter(len(p) for p in pws)
    return normalize(cnt)


def pattern_dist(pws):
    cnt = Counter(get_pattern(p) for p in pws)
    return normalize(cnt)


def euclid(d1, d2):
    keys = set(d1) | set(d2)
    return math.sqrt(sum((d1.get(k, 0) - d2.get(k, 0))**2 for k in keys))


def create_comparison_chart(length_distances, pattern_distances, save_to_file=False):
    """
    Tạo biểu đồ so sánh cho web API
    
    Args:
        length_distances: List of length distances
        pattern_distances: List of pattern distances  
        save_to_file: True nếu muốn save file, False nếu return base64
    
    Returns:
        base64 string của hình ảnh hoặc file path
    """
    try:
        labels = ['PagPassGPT', 'PassGPT', 'PassGAN']
        dist_length = [item['distance'] for item in length_distances]
        dist_pattern = [item['distance'] for item in pattern_distances]
        
        # Tạo biểu đồ
        x = np.arange(len(labels))
        width = 0.35
        
        # Tạo figure với explicit figsize
        plt.style.use('default')  # Reset style
        fig, ax = plt.subplots(figsize=(10, 6), facecolor='white')
        
        bars1 = ax.bar(x - width/2, dist_length, width, label='Length Distance', 
                      color='#ff9500', alpha=0.8)
        bars2 = ax.bar(x + width/2, dist_pattern, width, label='Pattern Distance', 
                      color='#ff6b47', alpha=0.8)
        
        # Styling
        ax.set_xlabel('Generated Models', fontsize=12, fontweight='bold')
        ax.set_ylabel('Euclidean Distance', fontsize=12, fontweight='bold')
        ax.set_title('Password Pattern Analysis: Length vs Pattern Distances to Original', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend(loc='upper right')
        
        # Thêm giá trị trên các cột
        def add_value_labels(bars):
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:.4f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom',
                           fontsize=9, fontweight='bold')
        
        add_value_labels(bars1)
        add_value_labels(bars2)
        
        # Grid cho dễ đọc
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        
        if save_to_file:
            # Save to file
            chart_path = f"static/charts/pattern_comparison_{int(time.time())}.png"
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
        print(f"Error creating comparison chart: {e}")
        traceback.print_exc()
        return None

def create_single_analysis_charts(top_lengths, top_patterns, filename="", save_to_file=False):
    """
    Tạo biểu đồ phân tích đơn cho web API
    
    Args:
        top_lengths: Top length distributions
        top_patterns: Top pattern distributions
        filename: Tên file để làm title
        save_to_file: True nếu muốn save file, False nếu return base64
    
    Returns:
        Dict chứa base64 strings của 2 biểu đồ
    """
    try:
        # Tạo 2 subplot
        plt.style.use('default')  # Reset style
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), facecolor='white')
        
        # Biểu đồ phân phối độ dài
        lengths = [item['length'] for item in top_lengths[:10]]
        length_counts = [item['count'] for item in top_lengths[:10]]
        
        bars1 = ax1.bar(range(len(lengths)), length_counts, color='#ff9500', alpha=0.8)
        ax1.set_xlabel('Password Length', fontweight='bold')
        ax1.set_ylabel('Count', fontweight='bold')
        ax1.set_title(f'Top 10 Password Length Distribution\n{filename}', fontweight='bold')
        ax1.set_xticks(range(len(lengths)))
        ax1.set_xticklabels(lengths)
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Thêm giá trị trên cột
        for i, bar in enumerate(bars1):
            height = bar.get_height()
            percentage = top_lengths[i]['frequency'] * 100
            ax1.annotate(f'{int(height)}\n({percentage:.1f}%)',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=8, fontweight='bold')
        
        # Biểu đồ phân phối pattern
        patterns = [item['pattern'] for item in top_patterns[:10]]
        pattern_counts = [item['count'] for item in top_patterns[:10]]
        
        bars2 = ax2.bar(range(len(patterns)), pattern_counts, color='#ff6b47', alpha=0.8)
        ax2.set_xlabel('Pattern Type', fontweight='bold')
        ax2.set_ylabel('Count', fontweight='bold')
        ax2.set_title(f'Top 10 Pattern Distribution\n{filename}', fontweight='bold')
        ax2.set_xticks(range(len(patterns)))
        ax2.set_xticklabels(patterns, rotation=45, ha='right')
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Thêm giá trị trên cột
        for i, bar in enumerate(bars2):
            height = bar.get_height()
            percentage = top_patterns[i]['frequency'] * 100
            ax2.annotate(f'{int(height)}\n({percentage:.1f}%)',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=8, fontweight='bold')
        
        plt.tight_layout()
        
        if save_to_file:
            # Save to file
            chart_path = f"static/charts/single_analysis_{int(time.time())}.png"
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
        print(f"Error creating single analysis charts: {e}")
        traceback.print_exc()
        return None

def main():
    parser = argparse.ArgumentParser(description='Compute and plot single and grouped bar charts of length & pattern distances')
    parser.add_argument('--plaintext', required=True, help='Original plaintext passwords')
    parser.add_argument('--DC_generated', required=True, help='PagPassGPT DC generated passwords')
    parser.add_argument('--PassGPT_plaintext', required=True, help='PassGPT generated passwords')
    parser.add_argument('--PassGAN_plaintext', required=True, help='PassGAN generated passwords')
    args = parser.parse_args()

    # load lists
    pws_orig    = load_passwords(args.plaintext)
    pws_dc      = load_passwords(args.DC_generated)
    pws_passgpt = load_passwords(args.PassGPT_plaintext)
    pws_passgan = load_passwords(args.PassGAN_plaintext)

    # compute distributions
    ld_orig    = length_dist(pws_orig)
    ld_dc      = length_dist(pws_dc)
    ld_passgpt = length_dist(pws_passgpt)
    ld_passgan = length_dist(pws_passgan)

    pd_orig    = pattern_dist(pws_orig)
    pd_dc      = pattern_dist(pws_dc)
    pd_passgpt = pattern_dist(pws_passgpt)
    pd_passgan = pattern_dist(pws_passgan)

    # compute Euclidean distances to original
    dist_length = [
        euclid(ld_orig, ld_dc),
        euclid(ld_orig, ld_passgpt),
        euclid(ld_orig, ld_passgan)
    ]
    dist_pattern = [
        euclid(pd_orig, pd_dc),
        euclid(pd_orig, pd_passgpt),
        euclid(pd_orig, pd_passgan)
    ]
    labels = ['DC_generated', 'PassGPT', 'PassGAN']

    # print distances
    print('=== Length distances (Euclidean) ===')
    for label, val in zip(labels, dist_length):
        print(f'{label:12s}: {val:.4f}')

    print('\n=== Pattern distances (Euclidean) ===')
    for label, val in zip(labels, dist_pattern):
        print(f'{label:12s}: {val:.4f}')

    # plot grouped bar chart
    x = np.arange(len(labels))  # label locations
    width = 0.35  # bar width

    fig, ax = plt.subplots(figsize=(8, 5))
    bars1 = ax.bar(x - width/2, dist_length, width, label='Length')
    bars2 = ax.bar(x + width/2, dist_pattern, width, label='Pattern')

    ax.set_xlabel('Generated Sets')
    ax.set_ylabel('Euclidean Distance')
    ax.set_title('Comparison of Length vs Pattern Distances to Original')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    main()
