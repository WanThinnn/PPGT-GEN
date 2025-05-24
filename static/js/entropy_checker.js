/* filepath: /mnt/d/Documents/UIT/Nam_3/HK2/NT522_AI-ATTT/PPGT-GEN/static/js/entropy_checker.js */
const form = document.getElementById('entropy-form');
const submitBtn = document.getElementById('submit-btn');
const cancelBtn = document.getElementById('cancel-btn');
const btnText = document.getElementById('btn-text');
const passwordInput = document.getElementById('password');
const fileInput = document.getElementById('password-file');
const togglePasswordBtn = document.getElementById('toggle-password');
const modeButtons = document.querySelectorAll('.mode-btn');
const modeInfos = document.querySelectorAll('.mode-info');

let currentMode = 'single';
let checkStartTime = null;
let isProcessing = false;
let currentController = null;

// Mode switching
modeButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    const mode = btn.dataset.mode;
    switchMode(mode);
  });
});

function switchMode(mode) {
  currentMode = mode;
  
  // Update active button
  modeButtons.forEach(btn => {
    btn.classList.toggle('active', btn.dataset.mode === mode);
  });
  
  // Update mode info
  modeInfos.forEach(info => {
    info.classList.toggle('active', info.classList.contains(`${mode}-mode`));
  });
  
  // Show/hide form elements
  const singleForm = document.querySelector('.single-mode-form');
  const fileForm = document.querySelector('.file-mode-form');
  
  if (mode === 'single') {
    singleForm.style.display = 'block';
    fileForm.style.display = 'none';
    passwordInput.required = true;
    fileInput.required = false;
    btnText.textContent = 'Phân tích entropy';
  } else {
    singleForm.style.display = 'none';
    fileForm.style.display = 'block';
    passwordInput.required = false;
    fileInput.required = true;
    btnText.textContent = 'Phân tích file';
  }
}

// Password toggle functionality
togglePasswordBtn.addEventListener('click', () => {
  const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
  passwordInput.setAttribute('type', type);
  togglePasswordBtn.textContent = type === 'password' ? '👁️ Hiện' : '🙈 Ẩn';
});

// Cancel button functionality
cancelBtn.addEventListener('click', async () => {
  if (!isProcessing) return;
  
  try {
    if (currentController) {
      currentController.abort();
    }
    
    resetToInitialState();
    
    const resultElement = document.getElementById('result');
    const statusBadge = document.getElementById('status-badge');
    
    resultElement.textContent = `❌ Quá trình phân tích đã bị hủy bởi người dùng\n\nThời gian hủy: ${new Date().toLocaleString()}`;
    statusBadge.textContent = 'Đã hủy';
    statusBadge.className = 'status-badge status-error';
    
    const checkTime = checkStartTime ? 
      Math.round((Date.now() - checkStartTime) / 1000) : 0;
    document.getElementById('check-time').textContent = `${checkTime}s`;
    
    showResult();
    
  } catch (error) {
    console.error('Error during cancellation:', error);
  }
});

function showResult() {
  document.getElementById('result-placeholder').classList.add('hidden');
  document.getElementById('result-content').classList.add('show');
  
  document.querySelector('.container').classList.add('has-result');
  
  const modeIndicator = document.getElementById('mode-indicator');
  const modeIcon = currentMode === 'single' ? '📊' : '📄';
  const modeText = currentMode === 'single' ? 'Đơn' : 'File';
  modeIndicator.textContent = `${modeIcon} ${modeText}`;
}

function hideResult() {
  document.getElementById('result-placeholder').classList.remove('hidden');
  document.getElementById('result-content').classList.remove('show');
  
  document.querySelector('.container').classList.remove('has-result');
}

function setProcessingState(processing) {
  isProcessing = processing;
  
  if (processing) {
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;
    cancelBtn.classList.add('show');
    btnText.textContent = currentMode === 'single' ? 'Đang phân tích...' : 'Đang phân tích file...';
  } else {
    submitBtn.classList.remove('loading');
    submitBtn.disabled = false;
    cancelBtn.classList.remove('show');
    const modeText = currentMode === 'single' ? 'Phân tích entropy' : 'Phân tích file';
    btnText.textContent = modeText;
  }
}

function resetToInitialState() {
  setProcessingState(false);
  checkStartTime = null;
  currentController = null;
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  
  if (isProcessing) return;
  
  checkStartTime = Date.now();
  setProcessingState(true);
  
  currentController = new AbortController();

  try {
    let data = {};
    let endpoint = '';
    let requestOptions = {
      method: 'POST',
      signal: currentController.signal
    };
    
    if (currentMode === 'single') {
      data = { password: passwordInput.value };
      endpoint = '/analyze_single_entropy';
      requestOptions.headers = {'Content-Type': 'application/json'};
      requestOptions.body = JSON.stringify(data);
    } else {
      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
      endpoint = '/analyze_file_entropy';
      requestOptions.body = formData;
    }

    const res = await fetch(endpoint, requestOptions);
    
    if (!res.ok) {
      throw new Error(`HTTP Error: ${res.status}`);
    }
    
    const result = await res.json();
    displayResult(result, true);

  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('Request was cancelled');
      return;
    }
    
    const checkTime = checkStartTime ? 
      Math.round((Date.now() - checkStartTime) / 1000) : 0;
    document.getElementById('check-time').textContent = `${checkTime}s`;
    
    document.getElementById('result').textContent = `❌ Lỗi: ${error.message}`;
    document.getElementById('status-badge').textContent = 'Lỗi';
    document.getElementById('status-badge').className = 'status-badge status-error';
    showResult();
  } finally {
    setProcessingState(false);
    currentController = null;
  }
});

function displayResult(result, isSuccess) {
  if (currentMode === 'file') {
    window.lastFileResult = result;
  }
  
  const checkTime = checkStartTime ? 
    Math.round((Date.now() - checkStartTime) / 1000) : 0;
  document.getElementById('check-time').textContent = `${checkTime}s`;
  
  const resultElement = document.getElementById('result');
  const statusBadge = document.getElementById('status-badge');
  
  if (currentMode === 'single') {
    // Single password entropy result
    let resultText = `📊 PHÂN TÍCH ENTROPY MẬT KHẨU ĐƠN\n`;
    resultText += `${'='.repeat(50)}\n\n`;
    resultText += `🔐 Mật khẩu: ${result.password}\n`;
    resultText += `📏 Độ dài: ${result.length} ký tự\n\n`;
    
    resultText += `📊 Phân tích Entropy:\n`;
    resultText += `  • Shannon Entropy: ${result.shannon_entropy.toFixed(2)} bits\n`;
    resultText += `  • Min-Entropy: ${result.min_entropy.toFixed(2)} bits\n`;
    resultText += `  • Max Entropy có thể: ${result.max_possible_entropy.toFixed(2)} bits\n`;
    resultText += `  • Tỷ lệ entropy: ${result.entropy_ratio.toFixed(2)}%\n\n`;
    
    resultText += `🔢 Phân phối ký tự:\n`;
    resultText += `  • Tổng ký tự duy nhất: ${result.unique_chars}\n`;
    resultText += `  • Ký tự thường: ${result.lowercase_count}\n`;
    resultText += `  • Ký tự hoa: ${result.uppercase_count}\n`;
    resultText += `  • Chữ số: ${result.digit_count}\n`;
    resultText += `  • Ký tự đặc biệt: ${result.special_count}\n\n`;
    
    if (result.char_frequency && result.char_frequency.length > 0) {
      resultText += `📈 Top 5 ký tự phổ biến:\n`;
      result.char_frequency.slice(0, 5).forEach((item, index) => {
        resultText += `  ${index + 1}. '${item.char}': ${item.count} lần (${item.frequency.toFixed(4)})\n`;
      });
    }
    
    resultElement.textContent = resultText;
    
    // Set status based on entropy ratio
    const entropyRatio = result.entropy_ratio;
    if (entropyRatio >= 80) {
      statusBadge.textContent = 'Cao';
      statusBadge.className = 'status-badge status-high';
    } else if (entropyRatio >= 60) {
      statusBadge.textContent = 'Trung bình';
      statusBadge.className = 'status-badge status-medium';
    } else {
      statusBadge.textContent = 'Thấp';
      statusBadge.className = 'status-badge status-low';
    }
  } else {
    // File entropy analysis result
    let resultText = `📄 BÁO CÁO PHÂN TÍCH ENTROPY FILE\n`;
    resultText += `Thời gian: ${result.timestamp}\n`;
    resultText += `File nguồn: ${result.filename}\n`;
    resultText += `${'='.repeat(50)}\n\n`;
    
    resultText += `📊 THỐNG KÊ TỔNG QUAN:\n`;
    resultText += `Tổng số mật khẩu: ${result.total_passwords}\n`;
    resultText += `Độ dài trung bình: ${result.avg_length.toFixed(2)} ký tự\n`;
    resultText += `Entropy trung bình: ${result.avg_entropy.toFixed(2)} bits\n`;
    resultText += `Entropy tối thiểu: ${result.min_entropy.toFixed(2)} bits\n`;
    resultText += `Entropy tối đa: ${result.max_entropy.toFixed(2)} bits\n\n`;
    
    resultText += `🔢 THỐNG KÊ KÝ TỰ:\n`;
    resultText += `Tổng số ký tự: ${result.total_chars}\n`;
    resultText += `Ký tự duy nhất: ${result.unique_chars}\n`;
    resultText += `Shannon entropy phân phối: ${result.char_distribution_entropy.toFixed(2)} bits\n`;
    resultText += `Min-entropy phân phối: ${result.char_min_entropy.toFixed(2)} bits\n\n`;
    
    resultText += `📈 PHÂN LOẠI KÝ TỰ:\n`;
    resultText += `Ký tự thường: ${result.lowercase_count}\n`;
    resultText += `Ký tự hoa: ${result.uppercase_count}\n`;
    resultText += `Chữ số: ${result.digit_count}\n`;
    resultText += `Ký tự đặc biệt: ${result.special_count}\n\n`;
    
    if (result.top_chars && result.top_chars.length > 0) {
      resultText += `🏆 Top 10 ký tự phổ biến:\n`;
      result.top_chars.forEach((item, index) => {
        resultText += `  ${index + 1}. '${item.char}': ${item.count} (${item.frequency.toFixed(4)})\n`;
      });
    }
    
    resultElement.textContent = resultText;
    
    // Set status based on average entropy
    const avgEntropy = result.avg_entropy;
    if (avgEntropy >= 40) {
      statusBadge.textContent = 'Cao';
      statusBadge.className = 'status-badge status-high';
    } else if (avgEntropy >= 25) {
      statusBadge.textContent = 'Trung bình';
      statusBadge.className = 'status-badge status-medium';
    } else {
      statusBadge.textContent = 'Thấp';
      statusBadge.className = 'status-badge status-low';
    }
  }
  
  showResult();
}

// Copy button functionality
document.getElementById('copy-btn').addEventListener('click', async () => {
  try {
    const resultElement = document.getElementById('result');
    await navigator.clipboard.writeText(resultElement.textContent);
    const btn = document.getElementById('copy-btn');
    const originalText = btn.textContent;
    btn.textContent = '✅ Copied!';
    setTimeout(() => {
      btn.textContent = originalText;
    }, 2000);
  } catch (err) {
    console.error('Failed to copy:', err);
  }
});

// Download button functionality
document.getElementById('download-btn').addEventListener('click', async () => {
  try {
    const content = document.getElementById('result').textContent;
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `entropy-analysis-${currentMode}-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    const btn = document.getElementById('download-btn');
    const originalText = btn.textContent;
    btn.textContent = '✅ Downloaded!';
    setTimeout(() => {
      btn.textContent = originalText;
    }, 2000);
  } catch (err) {
    console.error('Failed to download:', err);
  }
});

// Initialize default mode
switchMode('single');