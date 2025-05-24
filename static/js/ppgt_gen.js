/* filepath: /mnt/d/Documents/UIT/Nam_3/HK2/NT522_AI-ATTT/PPGT-GEN/static/js/strength_checker.js */
const form = document.getElementById('strength-form');
const submitBtn = document.getElementById('submit-btn');
const btnText = document.getElementById('btn-text');
const passwordInput = document.getElementById('password');
const fileInput = document.getElementById('password-file');
const togglePasswordBtn = document.getElementById('toggle-password');
const modeButtons = document.querySelectorAll('.mode-btn');
const modeInfos = document.querySelectorAll('.mode-info');

let currentMode = 'single'; // Default mode
let checkStartTime = null;

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
    btnText.textContent = 'Kiểm tra độ mạnh';
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

function showResult() {
  document.getElementById('result-placeholder').classList.add('hidden');
  document.getElementById('result-content').classList.add('show');
  
  // Expand container for better PC experience
  document.querySelector('.container').classList.add('has-result');
  
  // Update mode indicator
  const modeIndicator = document.getElementById('mode-indicator');
  const modeIcon = currentMode === 'single' ? '🔒' : '📄';
  const modeText = currentMode === 'single' ? 'Đơn' : 'File';
  modeIndicator.textContent = `${modeIcon} ${modeText}`;
}

function hideResult() {
  document.getElementById('result-placeholder').classList.remove('hidden');
  document.getElementById('result-content').classList.remove('show');
  
  // Remove expanded layout
  document.querySelector('.container').classList.remove('has-result');
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  
  checkStartTime = Date.now();
  
  // Show loading state
  submitBtn.classList.add('loading');
  btnText.textContent = `Đang kiểm tra...`;
  submitBtn.disabled = true;

  try {
    let data = {};
    let endpoint = '';
    
    if (currentMode === 'single') {
      data = { password: passwordInput.value };
      endpoint = '/check_single_password';
    } else {
      // Handle file upload
      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
      
      const res = await fetch('/check_password_file', {
        method: 'POST',
        body: formData
      });
      
      const result = await res.json();
      displayResult(result, res.ok);
      return;
    }

    const res = await fetch(endpoint, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    });

    const result = await res.json();
    displayResult(result, res.ok);

  } catch (error) {
    const checkTime = checkStartTime ? 
      Math.round((Date.now() - checkStartTime) / 1000) : 0;
    document.getElementById('check-time').textContent = `${checkTime}s`;
    
    document.getElementById('result').textContent = `Lỗi: ${error.message}`;
    document.getElementById('status-badge').textContent = 'Lỗi';
    document.getElementById('status-badge').className = 'status-badge status-error';
    showResult();
  } finally {
    resetButtonState();
    checkStartTime = null;
  }
});

function displayResult(result, isSuccess) {
  // Calculate check time
  const checkTime = checkStartTime ? 
    Math.round((Date.now() - checkStartTime) / 1000) : 0;
  document.getElementById('check-time').textContent = `${checkTime}s`;
  
  // Show result
  const resultElement = document.getElementById('result');
  const statusBadge = document.getElementById('status-badge');
  
  if (currentMode === 'single') {
    // Single password result
    let resultText = `Mật khẩu: ${result.password}\n\n`;
    resultText += `Trạng thái: ${result.is_strong ? '✅ Mạnh' : '❌ Yếu'}\n\n`;
    
    if (!result.is_strong && result.issues) {
      resultText += `Các vấn đề:\n`;
      result.issues.forEach(issue => {
        resultText += `  • ${issue}\n`;
      });
    }
    
    resultElement.textContent = resultText;
    statusBadge.textContent = result.is_strong ? 'Mạnh' : 'Yếu';
    statusBadge.className = result.is_strong ? 'status-badge status-strong' : 'status-badge status-weak';
  } else {
    // File analysis result
    let resultText = `📄 PHÂN TÍCH FILE MẬT KHẨU\n`;
    resultText += `${'='.repeat(50)}\n\n`;
    resultText += `📊 Thống kê tổng quan:\n`;
    resultText += `  • Tổng số mật khẩu: ${result.total_passwords}\n`;
    resultText += `  • Mật khẩu mạnh: ${result.strong_passwords} (${result.strong_percentage}%)\n`;
    resultText += `  • Mật khẩu yếu: ${result.weak_passwords} (${result.weak_percentage}%)\n\n`;
    
    if (result.common_issues && result.common_issues.length > 0) {
      resultText += `🔍 Các vấn đề phổ biến:\n`;
      result.common_issues.forEach(issue => {
        resultText += `  • ${issue.issue}: ${issue.count} lần\n`;
      });
      resultText += `\n`;
    }
    
    if (result.sample_weak_passwords && result.sample_weak_passwords.length > 0) {
      resultText += `📝 Mẫu mật khẩu yếu:\n`;
      result.sample_weak_passwords.slice(0, 10).forEach((pwd, index) => {
        resultText += `  ${index + 1}. ${pwd.password}\n`;
        resultText += `     Vấn đề: ${pwd.issues.join(', ')}\n`;
      });
    }
    
    resultElement.textContent = resultText;
    
    const strongPercent = parseFloat(result.strong_percentage);
    if (strongPercent >= 70) {
      statusBadge.textContent = 'Tốt';
      statusBadge.className = 'status-badge status-strong';
    } else if (strongPercent >= 40) {
      statusBadge.textContent = 'Trung bình';
      statusBadge.className = 'status-badge status-weak';
    } else {
      statusBadge.textContent = 'Yếu';
      statusBadge.className = 'status-badge status-error';
    }
  }
  
  showResult();
}

function resetButtonState() {
  submitBtn.classList.remove('loading');
  const modeText = currentMode === 'single' ? 'Kiểm tra độ mạnh' : 'Phân tích file';
  btnText.textContent = modeText;
  submitBtn.disabled = false;
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
document.getElementById('download-btn').addEventListener('click', () => {
  try {
    const content = document.getElementById('result').textContent;
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `password-check-${currentMode}-${Date.now()}.txt`;
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