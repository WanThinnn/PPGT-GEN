# app.py
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Tuple, Optional
from flask import Flask, jsonify, request, render_template, redirect, url_for
from flask_cors import CORS
from libanalyst.password_strength_checker import check_single_password
from libanalyst.password_entropy_checker import analyze_single_password, analyze_password_file
from libanalyst.password_evaluate_checker import evaluate_model
from libanalyst.password_pattern_checker import (
    load_passwords, get_pattern, length_dist, pattern_dist, euclid,
    create_comparison_chart, create_single_analysis_charts
)
from collections import Counter
from datetime import datetime
import tempfile
import os
import sys
import threading
import time
import signal
import atexit
import subprocess
import logging
import psutil
import traceback
import argparse, math, itertools
from collections import Counter
import matplotlib
matplotlib.use('Agg')  # Thêm backend cho server environment
import matplotlib.pyplot as plt
import numpy as np
import base64
import io
import os
import time

# Global variable để track running processes
running_processes = {}
process_lock = threading.Lock()
# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Thêm libppgt vào Python path
sys.path.insert(0, os.path.abspath("libppgt"))

app = Flask(__name__)
CORS(app)  # Cho phép CORS cho frontend

# Cấu hình Flask
app.config.update(
    JSON_AS_ASCII=False,
    JSON_SORT_KEYS=False,
    JSONIFY_PRETTYPRINT_REGULAR=True
)

# Thread pool để chạy các task nặng
executor = ThreadPoolExecutor(max_workers=4)

class PathConverter:
    """Xử lý chuyển đổi đường dẫn giữa Windows và WSL"""
    
    @staticmethod
    def win_to_wsl(win_path: str) -> str:
        """Chuyển đường dẫn Windows sang WSL"""
        if not win_path or ':' not in win_path:
            return win_path
        
        try:
            # Chuẩn hóa đường dẫn
            win_path = win_path.strip().replace('\\', '/')
            
            # Tách drive và path
            parts = win_path.split(':', 1)
            if len(parts) != 2:
                return win_path
                
            drive = parts[0].lower()
            path = parts[1].strip('/')
            
            wsl_path = f"/mnt/{drive}/{path}" if path else f"/mnt/{drive}"
            logger.debug(f"Converted {win_path} -> {wsl_path}")
            return wsl_path
            
        except Exception as e:
            logger.error(f"Path conversion error: {e}")
            return win_path
    
    @staticmethod
    def validate_path(path: str, path_type: str = "file") -> bool:  
        """Kiểm tra đường dẫn có tồn tại không"""
        try:
            if path_type == "file":
                return os.path.isfile(path)
            elif path_type == "dir":
                return os.path.isdir(path)
            else:
                return os.path.exists(path)
        except Exception:
            return False
        
class ProcessRunner:
    """Chạy subprocess một cách an toàn và hiệu quả"""
    
    @staticmethod
    def run_command(cmd_args: list, timeout: int = 3600, process_id: str = None) -> Tuple[int, str]:
        """
        Chạy command với timeout và logging
        
        Args:
            cmd_args: Danh sách arguments
            timeout: Timeout tính bằng giây (mặc định 1 giờ)
            process_id: ID để track process (để có thể cancel)
            
        Returns:
            Tuple[returncode, output]
        """
        process = None
        try:
            logger.info(f"Executing command: {' '.join(cmd_args)}")
            
            process = subprocess.Popen(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                preexec_fn=os.setsid if os.name != 'nt' else None  # Tạo process group
            )
            
            # Track process nếu có process_id
            if process_id:
                with process_lock:
                    running_processes[process_id] = process
                logger.info(f"Process {process_id} started with PID: {process.pid}")
            
            try:
                # Đọc output theo real-time và check cancellation
                output_lines = []
                start_time = time.time()
                
                while True:
                    # Check nếu process bị cancel
                    with process_lock:
                        if process_id and process_id not in running_processes:
                            logger.info(f"Process {process_id} was cancelled")
                            return -2, "Process was cancelled by user"
                    
                    # Check timeout
                    if time.time() - start_time > timeout:
                        logger.warning(f"Process {process_id} timed out")
                        if process.poll() is None:
                            ProcessRunner._kill_process_tree(process)
                        return -1, f"Process timed out after {timeout} seconds"
                    
                    # Check if process finished
                    if process.poll() is not None:
                        # Process finished, read remaining output
                        remaining_output = process.stdout.read()
                        if remaining_output:
                            output_lines.append(remaining_output)
                        break
                    
                    # Read available output
                    try:
                        line = process.stdout.readline()
                        if line:
                            output_lines.append(line)
                    except:
                        pass
                    
                    time.sleep(0.1)  # Short sleep to prevent busy waiting
                
                output = ''.join(output_lines)
                returncode = process.returncode
                
                logger.info(f"Command completed with return code: {returncode}")
                return returncode, output
                
            except Exception as e:
                logger.error(f"Error during process execution: {e}")
                if process and process.poll() is None:
                    ProcessRunner._kill_process_tree(process)
                return -1, f"Error during execution: {str(e)}"
                
        except Exception as e:
            logger.error(f"Error starting process: {e}")
            return -1, f"Error starting process: {str(e)}"
        finally:
            # Remove from tracking
            if process_id:
                with process_lock:
                    running_processes.pop(process_id, None)
    
    @staticmethod
    def _kill_process_tree(process):
        """Kill process và tất cả child processes"""
        try:
            if os.name == 'nt':  # Windows
                # Windows: kill process tree
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)], 
                             capture_output=True)
            else:  # Unix/Linux
                # Unix: kill process group
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    time.sleep(2)
                    # Force kill nếu chưa chết
                    if process.poll() is None:
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass  # Process already terminated
                    
        except Exception as e:
            logger.error(f"Error killing process tree: {e}")
            # Fallback: kill process directly
            try:
                process.terminate()
                time.sleep(2)
                if process.poll() is None:
                    process.kill()
            except:
                pass
class RequestValidator:
    """Validate request parameters"""
    
    @staticmethod
    def validate_dc_gen_params(params: Dict[str, Any]) -> Optional[str]:
        """DC generation validation - giống như normal gen"""
        return RequestValidator.validate_normal_gen_params(params)
    
    @staticmethod
    def validate_normal_gen_params(params: Dict[str, Any]) -> Optional[str]:
        """Validate normal generation parameters"""
        required_keys = ["output_path", "generate_num", "batch_size", "gpu_num", "gpu_index"]
        
        for key in required_keys:
            if key not in params:
                return f"Missing required parameter: {key}"
        
        # Kiểm tra kiểu dữ liệu số
        numeric_fields = ["generate_num", "batch_size", "gpu_num", "gpu_index"]
        for field in numeric_fields:
            try:
                params[field] = int(params[field])
            except (ValueError, TypeError):
                return f"Invalid numeric value for {field}: {params[field]}"
        
        return None
    @staticmethod
    def validate_normal_gen_params(params: Dict[str, Any]) -> Optional[str]:
        """Validate normal generation parameters"""
        required_keys = ["output_path", "generate_num", "batch_size", "gpu_num", "gpu_index"]
        
        for key in required_keys:
            if key not in params:
                return f"Missing required parameter: {key}"
        
        # Kiểm tra kiểu dữ liệu số
        numeric_fields = ["generate_num", "batch_size", "gpu_num", "gpu_index"]
        for field in numeric_fields:
            try:
                params[field] = int(params[field])
            except (ValueError, TypeError):
                return f"Invalid numeric value for {field}: {params[field]}"
        
        return None
###################### GUI ######################

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}")
    return jsonify({"error": "An unexpected error occurred"}), 500

# Routes
@app.route("/")
def index():
    """Trang chủ với menu chọn tính năng"""
    return render_template('index.html')

@app.route("/ppgt_gen")
def ppgt_gen_page():
    """Trang PPGT Generator duy nhất"""
    return render_template("ppgt_gen.html")


@app.route('/strength_checker')
def strength_checker():
    return render_template('strength_checker.html')


@app.route('/entropy_checker')
def entropy_checker():
    return render_template('entropy_checker.html')

@app.route('/evaluate_checker')
def evaluate_checker():
    return render_template('evaluate_checker.html')

@app.route('/pattern_checker')
def pattern_checker():
    return render_template('pattern_checker.html')

@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "memory_usage": f"{psutil.virtual_memory().percent}%",
        "cpu_usage": f"{psutil.cpu_percent()}%",
        "disk_usage": f"{psutil.disk_usage('/').percent}%"
    })
######################### CALL API #########################
@app.route("/dc_generate", methods=["POST"])    
def dc_generate():
    """DC Generation API endpoint"""
    try:
        # Generate unique process ID
        process_id = f"dc_gen_{threading.current_thread().ident}_{int(time.time())}"
        
        # Parse request
        params = request.get_json(silent=True)
        if not params:
            return jsonify({"error": "Missing JSON body"}), 400
        
        # Validate parameters
        error = RequestValidator.validate_dc_gen_params(params)
        if error:
            return jsonify({"error": error}), 400
        
        model_path = os.path.abspath("model/last-step/")
        # Convert paths
        params["cleaned_dataset"] = PathConverter.win_to_wsl(params["cleaned_dataset"])
        params["model_path"] = PathConverter.win_to_wsl(model_path)
        params["output_path"] = PathConverter.win_to_wsl(params["output_path"])
        
        # Validate file existence
        if not PathConverter.validate_path(params["cleaned_dataset"], "file"):
            return jsonify({"error": f"Dataset not found: {params['cleaned_dataset']}"}), 400
        
        # Ensure output directory exists
        os.makedirs(params["output_path"], exist_ok=True)
        
        logger.info(f"Starting DC generation with params: {params}")
        logger.info(f"Process ID: {process_id}")
        
        # Step 1: Get pattern rate với process tracking
        cmd1 = [
            sys.executable, "libppgt/get_pattern_rate.py",
            "--dataset_path", params["cleaned_dataset"]
        ]
        rc1, out1 = ProcessRunner.run_command(cmd1, process_id=f"{process_id}_step1")
        
        if rc1 == -2:
            return jsonify({
                "success": False,
                "message": "Pattern rate step was cancelled by user",
                "cancelled": True,
                "step": "get_pattern_rate",
                "process_id": process_id
            }), 200
        
        if rc1 != 0:
            logger.error(f"Pattern rate step failed: {out1}")
            return jsonify({
                "error": "Pattern rate calculation failed",
                "step": "get_pattern_rate",
                "returncode": rc1,
                "output": out1
            }), 500
               # Debug: Kiểm tra patterns file
        patterns_file = os.path.abspath("patterns.txt")
        if os.path.exists(patterns_file):
            with open(patterns_file, 'r', encoding='utf-8', errors='ignore') as f:
                patterns_content = f.read()
                patterns_lines = len(patterns_content.splitlines())
                logger.info(f"Patterns file exists with {patterns_lines} lines")
                logger.info(f"First few lines: {patterns_content[:200]}")
        else:
            logger.error("Patterns file not found!")
            return jsonify({
                "success": False,
                "message": "Patterns file was not created by get_pattern_rate.py",
                "step": "patterns_validation"
            }), 500
        # Step 2: DC Generation với process tracking
        patterns_file = os.path.abspath("patterns.txt")  # Đường dẫn patterns file
        cmd2 = [
            sys.executable, "libppgt/DC-GEN.py",
            "--model_path", params["model_path"],
            "--pattern_path", patterns_file,  # THÊM DÒNG NÀY - QUAN TRỌNG!
            "--output_path", params["output_path"],
            "--generate_num", str(params["generate_num"]),
            "--batch_size", str(params["batch_size"]),
            "--gpu_num", str(params["gpu_num"]),
            "--gpu_index", str(params["gpu_index"])
        ]
        rc2, out2 = ProcessRunner.run_command(cmd2, process_id=f"{process_id}_step2")
        
        if rc2 == -2:
            return jsonify({
                "success": False,
                "message": "DC generation step was cancelled by user",
                "cancelled": True,
                "step": "DC-GEN",
                "process_id": process_id
            }), 200
        
        if rc2 != 0:
            logger.error(f"DC generation step failed: {out2}")
            return jsonify({
                "error": "DC generation failed",
                "step": "DC-GEN",
                "returncode": rc2,
                "output": out2
            }), 500
        
        result = {
            "success": True,
            "message": "DC generation completed successfully",
            "steps": {
                "pattern_rate": {
                    "returncode": rc1,
                    "output": out1
                },
                "dc_generation": {
                    "returncode": rc2,
                    "output": out2
                }
            },
            "output_directory": os.path.join(params["output_path"], str(params["generate_num"])),
            "parameters": params,
            "process_id": process_id
        }
        
        logger.info("DC generation completed successfully")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"DC generation error: {e}")
        return jsonify({"error": f"DC generation failed: {str(e)}"}), 500
    
    
@app.route("/normal_generate", methods=["POST"])
def normal_generate():
    """Normal Generation API endpoint"""
    try:
        # Generate unique process ID
        process_id = f"normal_gen_{threading.current_thread().ident}_{int(time.time())}"
        
        # Parse request
        params = request.get_json(silent=True)
        if not params:
            return jsonify({"error": "Missing JSON body"}), 400
        
        # Validate parameters
        error = RequestValidator.validate_normal_gen_params(params)
        if error:
            return jsonify({"error": error}), 400
        
        # Set default vocab file if not provided
        default_vocab = os.path.abspath("libppgt/tokenizer/vocab.json")
        vocab_path = params.get("vocabfile_path", default_vocab)
        model_path = os.path.abspath("model/last-step/")
        
        # Convert paths
        params["model_path"] = PathConverter.win_to_wsl(model_path)
        params["output_path"] = PathConverter.win_to_wsl(params["output_path"])
        params["vocabfile_path"] = PathConverter.win_to_wsl(vocab_path)
        
        if not PathConverter.validate_path(params["vocabfile_path"], "file"):
            return jsonify({"error": f"Vocab file not found: {params['vocabfile_path']}"}), 400
        
        # Ensure output directory exists
        os.makedirs(params["output_path"], exist_ok=True)
        
        logger.info(f"Starting normal generation with params: {params}")
        logger.info(f"Process ID: {process_id}")
        
        # Run normal generation với process tracking
        cmd = [
            sys.executable, "libppgt/normal-gen.py",
            "--model_path", params["model_path"],
            "--vocabfile_path", params["vocabfile_path"],
            "--output_path", params["output_path"],
            "--generate_num", str(params["generate_num"]),
            "--batch_size", str(params["batch_size"]),
            "--gpu_num", str(params["gpu_num"]),
            "--gpu_index", str(params["gpu_index"])
        ]
        
        # QUAN TRỌNG: Thêm process_id vào đây
        rc, output = ProcessRunner.run_command(cmd, process_id=process_id)
        
        # Check nếu process bị cancel
        if rc == -2:
            return jsonify({
                "success": False,
                "message": "Process was cancelled by user",
                "cancelled": True,
                "process_id": process_id
            }), 200
        
        if rc != 0:
            logger.error(f"Normal generation failed: {output}")
            return jsonify({
                "error": "Normal generation failed",
                "step": "Normal-GEN",
                "returncode": rc,
                "output": output
            }), 500
        
        result = {
            "success": True,
            "message": "Normal generation completed successfully",
            "step": "normal_generation",
            "returncode": rc,
            "output": output,
            "output_directory": os.path.join(params["output_path"], str(params["generate_num"])),
            "parameters": params,
            "process_id": process_id
        }
        
        logger.info("Normal generation completed successfully")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Normal generation error: {e}")
        return jsonify({"error": f"Normal generation failed: {str(e)}"}), 500


@app.route("/cancel_generation", methods=["POST"])
def cancel_generation():
    """Cancel running generation processes"""
    try:
        cancelled_count = 0
        cancelled_processes = []
        
        # Log tình trạng hiện tại
        with process_lock:
            logger.info(f"Current tracked processes: {list(running_processes.keys())}")
            for pid, process in running_processes.items():
                logger.info(f"Process {pid}: PID={process.pid}, Status={'running' if process.poll() is None else 'finished'}")
        
        with process_lock:
            # Cancel all running processes
            for process_id, process in list(running_processes.items()):
                try:
                    if process.poll() is None:  # Process is still running
                        logger.info(f"Cancelling process: {process_id} (PID: {process.pid})")
                        
                        # Kill process tree
                        ProcessRunner._kill_process_tree(process)
                        
                        cancelled_count += 1
                        cancelled_processes.append(process_id)
                        
                        # Remove from tracking immediately
                        running_processes.pop(process_id, None)
                        
                    else:
                        logger.info(f"Process {process_id} already finished, removing from tracking")
                        running_processes.pop(process_id, None)
                        
                except Exception as e:
                    logger.error(f"Error cancelling process {process_id}: {e}")
        
        logger.info(f"Successfully cancelled {cancelled_count} processes: {cancelled_processes}")
        
        return jsonify({
            "success": True,
            "message": f"Cancelled {cancelled_count} running processes",
            "cancelled_count": cancelled_count,
            "cancelled_processes": cancelled_processes
        })
        
    except Exception as e:
        logger.error(f"Error cancelling processes: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/status")
def get_status():
    """Get current status of running processes"""
    try:
        with process_lock:
            active_processes = {}
            total_tracked = len(running_processes)
            
            # Check which processes are actually still running
            for process_id, process in list(running_processes.items()):
                if process.poll() is None:
                    active_processes[process_id] = {
                        "pid": process.pid,
                        "status": "running"
                    }
                else:
                    # Remove finished processes from tracking
                    running_processes.pop(process_id, None)
            
            running_count = len(active_processes)
            
        return jsonify({
            "running_processes": running_count,
            "total_tracked": total_tracked,
            "active_processes": active_processes
        })
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/check_single_password', methods=['POST'])
def check_single_password_api():
    try:
        data = request.get_json()
        password = data.get('password', '')
        
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        is_strong, issues = check_single_password(password)
        
        return jsonify({
            'password': password,
            'is_strong': is_strong,
            'issues': issues
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/check_password_file', methods=['POST'])
def check_password_file_api():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as temp_file:
            content = file.read().decode('utf-8')
            temp_file.write(content)
            temp_filename = temp_file.name
        
        try:
            # Read and analyze passwords
            passwords = content.splitlines()
            # Lọc bỏ dòng trống
            valid_passwords = [p.strip() for p in passwords if p.strip()]
            total_passwords = len(valid_passwords)
            
            if total_passwords == 0:
                return jsonify({'error': 'File is empty or contains no valid passwords'}), 400
            
            # Analyze each password
            results = []
            strong_count = 0
            issues_counter = Counter()
            
            for password in valid_passwords:
                is_strong, issues = check_single_password(password)
                results.append({
                    'password': password,
                    'is_strong': is_strong,
                    'issues': issues
                })
                
                if is_strong:
                    strong_count += 1
                else:
                    # Đếm các vấn đề
                    for issue in issues:
                        issues_counter[issue] += 1
            
            weak_count = total_passwords - strong_count
            
            # Tính phần trăm
            strong_percentage = round((strong_count/total_passwords*100), 1)
            weak_percentage = round((weak_count/total_passwords*100), 1)
            
            # Get common issues (sắp xếp theo tần suất)
            common_issues = [
                {'issue': issue, 'count': count}
                for issue, count in issues_counter.most_common()
            ]
            
            # Get sample weak passwords (lấy 10 mẫu đầu tiên)
            weak_passwords = [r for r in results if not r['is_strong']]
            sample_weak = weak_passwords[:10]
            
            # Tạo timestamp cho báo cáo
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return jsonify({
                'timestamp': timestamp,
                'filename': file.filename,
                'total_passwords': total_passwords,
                'strong_passwords': strong_count,
                'weak_passwords': weak_count,
                'strong_percentage': strong_percentage,
                'weak_percentage': weak_percentage,
                'common_issues': common_issues,
                'sample_weak_passwords': sample_weak,
                'success': True
            })
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Global variable để track password checking processes
password_check_processes = {}
@app.route('/cancel_password_check', methods=['POST'])
def cancel_password_check():
    """Cancel password checking processes (nếu cần thiết cho future implementation)"""
    try:
        # Hiện tại password check thường rất nhanh nên không cần cancel thực sự
        # Nhưng có thể implement sau này cho file lớn
        return jsonify({
            "success": True,
            "message": "Password check cancellation noted"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze_single_entropy', methods=['POST'])
def analyze_single_entropy_api():
    try:
        data = request.get_json()
        password = data.get('password', '')
        
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        result = analyze_single_password(password)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze_file_entropy', methods=['POST'])
def analyze_file_entropy_api():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as temp_file:
            content = file.read().decode('utf-8')
            temp_file.write(content)
            temp_filename = temp_file.name
        
        try:
            result = analyze_password_file(temp_filename)
            
            if 'error' in result:
                return jsonify(result), 400
            
            # Add metadata
            result['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            result['filename'] = file.filename
            
            return jsonify(result)
        
        finally:
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/evaluate_password_model', methods=['POST'])
def evaluate_password_model_api():
    try:
        # Log để debug
        logger.info(f"Received request - Files: {list(request.files.keys())}, Form: {dict(request.form)}")
        
        if 'test_file' not in request.files:
            logger.error("No test_file in request.files")
            return jsonify({'error': 'No test file uploaded'}), 400
        
        test_file = request.files['test_file']
        gen_path = request.form.get('gen_path', '')
        is_normal = request.form.get('is_normal', 'true').lower() == 'true'
        
        logger.info(f"Form data - gen_path: '{gen_path}', is_normal: '{is_normal}'")
        
        if test_file.filename == '':
            logger.error("Empty test file name")
            return jsonify({'error': 'No test file selected'}), 400
        
        if not gen_path.strip():
            logger.error(f"Empty gen_path: '{gen_path}'")
            return jsonify({'error': 'Generated files path is required'}), 400
        
        # Convert Windows path to WSL path if needed
        gen_path = PathConverter.win_to_wsl(gen_path.strip())
        logger.info(f"Converted gen_path: '{gen_path}'")
        
        # Save test file temporarily
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as temp_file:
            content = test_file.read().decode('utf-8')
            temp_file.write(content)
            test_filename = temp_file.name
        
        logger.info(f"Saved test file to: {test_filename}")
        
        try:
            result = evaluate_model(test_filename, gen_path, is_normal)
            
            logger.info(f"evaluate_model result: {result}")
            
            if 'error' in result:
                logger.error(f"Error in evaluate_model: {result['error']}")
                return jsonify(result), 400
            
            # Add metadata
            result['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            result['test_file'] = test_file.filename
            result['gen_path'] = gen_path
            result['is_normal'] = is_normal
            
            logger.info("evaluate_password_model completed successfully")
            return jsonify(result)
        
        finally:
            if os.path.exists(test_filename):
                os.unlink(test_filename)
                logger.info(f"Cleaned up temp file: {test_filename}")
    
    except Exception as e:
        logger.error(f"Exception in evaluate_password_model: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/compare_password_patterns', methods=['POST'])
def compare_password_patterns_api():
    try:
        logger.info("Starting compare_password_patterns API")
        
        # Check if all files are uploaded
        required_files = ['plaintext_file', 'dc_file', 'passgpt_file', 'passgan_file']
        for file_key in required_files:
            if file_key not in request.files:
                logger.error(f"Missing {file_key}")
                return jsonify({'error': f'Missing {file_key}'}), 400
            if request.files[file_key].filename == '':
                logger.error(f"No {file_key} selected")
                return jsonify({'error': f'No {file_key} selected'}), 400
        
        logger.info("All files validated successfully")
        
        # Save uploaded files temporarily
        temp_files = {}
        try:
            for file_key in required_files:
                file = request.files[file_key]
                with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as temp_file:
                    content = file.read().decode('utf-8')
                    temp_file.write(content)
                    temp_files[file_key] = temp_file.name
                logger.info(f"Saved {file_key} to {temp_file.name}")
            
            # Load passwords using functions from password_pattern_checker.py
            logger.info("Loading passwords from files")
            pws_orig = load_passwords(temp_files['plaintext_file'])
            pws_dc = load_passwords(temp_files['dc_file'])
            pws_passgpt = load_passwords(temp_files['passgpt_file'])
            pws_passgan = load_passwords(temp_files['passgan_file'])
            
            logger.info(f"Loaded passwords: orig={len(pws_orig)}, dc={len(pws_dc)}, passgpt={len(pws_passgpt)}, passgan={len(pws_passgan)}")
            
            if not all([pws_orig, pws_dc, pws_passgpt, pws_passgan]):
                return jsonify({'error': 'One or more files contain no valid passwords'}), 400
            
            # Compute distributions using existing functions
            logger.info("Computing distributions")
            ld_orig = length_dist(pws_orig)
            ld_dc = length_dist(pws_dc)
            ld_passgpt = length_dist(pws_passgpt)
            ld_passgan = length_dist(pws_passgan)
            
            pd_orig = pattern_dist(pws_orig)
            pd_dc = pattern_dist(pws_dc)
            pd_passgpt = pattern_dist(pws_passgpt)
            pd_passgan = pattern_dist(pws_passgan)
            
            # Compute Euclidean distances to original using existing function
            logger.info("Computing Euclidean distances")
            length_distances = [
                {'model': 'DC_generated', 'distance': euclid(ld_orig, ld_dc)},
                {'model': 'PassGPT', 'distance': euclid(ld_orig, ld_passgpt)},
                {'model': 'PassGAN', 'distance': euclid(ld_orig, ld_passgan)}
            ]
            
            pattern_distances = [
                {'model': 'DC_generated', 'distance': euclid(pd_orig, pd_dc)},
                {'model': 'PassGPT', 'distance': euclid(pd_orig, pd_passgpt)},
                {'model': 'PassGAN', 'distance': euclid(pd_orig, pd_passgan)}
            ]
            
            # Tạo biểu đồ so sánh
            logger.info("Creating comparison chart")
            chart_base64 = create_comparison_chart(length_distances, pattern_distances, save_to_file=False)
            if chart_base64 is None:
                logger.warning("Failed to create chart, continuing without chart")
            
            result = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'length_distances': length_distances,
                'pattern_distances': pattern_distances,
                'chart': chart_base64,  # Có thể None nếu lỗi
                'stats': {
                    'original_passwords': len(pws_orig),
                    'dc_passwords': len(pws_dc),
                    'passgpt_passwords': len(pws_passgpt),
                    'passgan_passwords': len(pws_passgan)
                }
            }
            
            logger.info("compare_password_patterns completed successfully")
            return jsonify(result)
        
        finally:
            # Clean up temp files
            for temp_file in temp_files.values():
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                        logger.info(f"Cleaned up {temp_file}")
                except Exception as e:
                    logger.error(f"Error cleaning up {temp_file}: {e}")
    
    except Exception as e:
        logger.error(f"Error in compare_password_patterns: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/analyze_password_patterns', methods=['POST'])
def analyze_password_patterns_api():
    try:
        logger.info("Starting analyze_password_patterns API")
        
        if 'password_file' not in request.files:
            return jsonify({'error': 'No password file uploaded'}), 400
        
        file = request.files['password_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        logger.info(f"Processing file: {file.filename}")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as temp_file:
            content = file.read().decode('utf-8')
            temp_file.write(content)
            temp_filename = temp_file.name
        
        try:
            # Load passwords using existing function
            logger.info("Loading passwords from file")
            passwords = load_passwords(temp_filename)
            
            if not passwords:
                return jsonify({'error': 'No valid passwords found in file'}), 400
            
            logger.info(f"Loaded {len(passwords)} passwords")
            
            # Compute length and pattern distributions using existing functions
            logger.info("Computing distributions")
            ld = length_dist(passwords)
            pd = pattern_dist(passwords)
            
            # Additional statistics
            avg_length = sum(len(p) for p in passwords) / len(passwords)
            unique_patterns = len(pd)
            
            # Top lengths and patterns
            length_counter = Counter(len(p) for p in passwords)
            pattern_counter = Counter(get_pattern(p) for p in passwords)
            
            top_lengths = [
                {
                    'length': length,
                    'count': count,
                    'frequency': count / len(passwords)
                }
                for length, count in length_counter.most_common(10)
            ]
            
            top_patterns = [
                {
                    'pattern': pattern,
                    'count': count,
                    'frequency': count / len(passwords)
                }
                for pattern, count in pattern_counter.most_common(15)
            ]
            
            # Tạo biểu đồ phân tích
            logger.info("Creating analysis charts")
            chart_base64 = create_single_analysis_charts(top_lengths, top_patterns, 
                                                        filename=file.filename, save_to_file=False)
            if chart_base64 is None:
                logger.warning("Failed to create charts, continuing without charts")
            
            result = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'filename': file.filename,
                'total_passwords': len(passwords),
                'avg_length': avg_length,
                'unique_patterns': unique_patterns,
                'top_lengths': top_lengths,
                'top_patterns': top_patterns,
                'chart': chart_base64  # Có thể None nếu lỗi
            }
            
            logger.info("analyze_password_patterns completed successfully")
            return jsonify(result)
        
        finally:
            try:
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)
                    logger.info(f"Cleaned up {temp_filename}")
            except Exception as e:
                logger.error(f"Error cleaning up {temp_filename}: {e}")
    
    except Exception as e:
        logger.error(f"Error in analyze_password_patterns: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# Set font để tránh warning
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']

def create_comparison_chart(length_distances, pattern_distances, save_to_file=False):
    """
    Tạo biểu đồ so sánh cho web API
    """
    try:
        labels = ['DC Generated', 'PassGPT', 'PassGAN']
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
        import traceback
        traceback.print_exc()
        return None

def create_single_analysis_charts(top_lengths, top_patterns, filename="", save_to_file=False):
    """
    Tạo biểu đồ phân tích đơn cho web API
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
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Cleanup function để kill processes khi app shutdown
    def cleanup_processes():
        logger.info("Cleaning up running processes...")
        with process_lock:
            for process_id, process in running_processes.items():
                try:
                    if process.poll() is None:
                        logger.info(f"Terminating process: {process_id}")
                        ProcessRunner._kill_process_tree(process)
                except Exception as e:
                    logger.error(f"Error terminating process {process_id}: {e}")
            running_processes.clear()
    
    atexit.register(cleanup_processes)
    
    # Signal handlers để cleanup khi Ctrl+C
    def signal_handler(signum, frame):
        logger.info("Received interrupt signal, cleaning up...")
        cleanup_processes()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Kiểm tra môi trường
    logger.info("Starting Flask application...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Production mode
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True,
        use_reloader=False
    )