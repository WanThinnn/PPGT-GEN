/* filepath: /mnt/d/Documents/UIT/Nam_3/HK2/NT522_AI-ATTT/PPGT-GEN/static/js/strength_checker.js */
const form = document.getElementById('strength-form');
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
let currentController = null; // AbortController cho fetch

// Thêm biến global để lưu trữ mật khẩu mạnh
let strongPasswordsData = {
  passwords: [],
  filename: '',
  count: 0
};

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

// Cancel button functionality
cancelBtn.addEventListener('click', async () => {
  if (!isProcessing) return;
  
  try {
    // Abort current fetch request
    if (currentController) {
      currentController.abort();
    }
    
    // Reset UI state
    resetToInitialState();
    
    // Show cancelled message
    const resultElement = document.getElementById('result');
    const statusBadge = document.getElementById('status-badge');
    
    resultElement.textContent = `❌ Quá trình kiểm tra đã bị hủy bởi người dùng\n\nThời gian hủy: ${new Date().toLocaleString()}`;
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

function setProcessingState(processing) {
  isProcessing = processing;
  
  if (processing) {
    // Show loading state
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;
    cancelBtn.classList.add('show');
    btnText.textContent = currentMode === 'single' ? 'Đang kiểm tra...' : 'Đang phân tích...';
  } else {
    // Reset button state
    submitBtn.classList.remove('loading');
    submitBtn.disabled = false;
    cancelBtn.classList.remove('show');
    const modeText = currentMode === 'single' ? 'Kiểm tra độ mạnh' : 'Phân tích file';
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
  
  if (isProcessing) return; // Prevent double submission
  
  checkStartTime = Date.now();
  setProcessingState(true);
  
  // Create AbortController for cancellation
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
      endpoint = '/check_single_password';
      requestOptions.headers = {'Content-Type': 'application/json'};
      requestOptions.body = JSON.stringify(data);
    } else {
      // Handle file upload
      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
      endpoint = '/check_password_file';
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
      // Request was cancelled, don't show error
      console.log('Request was cancelled');
      return;
    }
    
    // Show error result
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

function toggleStrongPasswordsInfo() {
  const info = document.getElementById('strong-passwords-info');
  if (info.style.display === 'none') {
    info.style.display = 'block';
  } else {
    info.style.display = 'none';
  }
}

function toggleStrongPasswordsPreview() {
  const preview = document.getElementById('strong-passwords-preview');
  const btn = document.getElementById('preview-strong-btn');
  
  if (preview.style.display === 'none') {
    preview.style.display = 'block';
    btn.innerHTML = '🙈 Ẩn';
    displayStrongPasswordsList();
  } else {
    preview.style.display = 'none';
    btn.innerHTML = '👁️ Xem trước';
  }
}

function displayStrongPasswordsList() {
  const listContainer = document.getElementById('strong-passwords-list');
  
  if (strongPasswordsData.passwords.length === 0) {
    listContainer.innerHTML = '<p class="no-passwords">Không có mật khẩu mạnh nào.</p>';
    return;
  }
  
  let html = '';
  strongPasswordsData.passwords.forEach((password, index) => {
    html += `<div class="password-item">
      <span class="password-text">${escapeHtml(password)}</span>
      <button class="copy-password-btn" onclick="copyPassword('${escapeHtml(password)}')" title="Copy mật khẩu">📋</button>
    </div>`;
  });
  
  listContainer.innerHTML = html;
}

function copyPassword(password) {
  navigator.clipboard.writeText(password).then(() => {
    showNotification('Đã copy mật khẩu!', 'success');
  }).catch(() => {
    showNotification('Không thể copy mật khẩu', 'error');
  });
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

async function downloadStrongPasswords() {
  if (strongPasswordsData.passwords.length === 0) {
    showNotification('Không có mật khẩu mạnh để tải về', 'error');
    return;
  }
  
  try {
    const response = await fetch('/download_strong_passwords', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        strong_passwords: strongPasswordsData.passwords,
        filename: strongPasswordsData.filename
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP Error: ${response.status}`);
    }
    
    // Tạo blob từ response
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    
    // Tạo link download
    const a = document.createElement('a');
    a.href = url;
    a.download = `strong_passwords_${Date.now()}.txt`;
    a.style.display = 'none';
    
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showNotification(`Đã tải về ${strongPasswordsData.count} mật khẩu mạnh!`, 'success');
    
    // Update button text temporarily
    const btn = document.getElementById('download-strong-btn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '✅ Đã tải về!';
    setTimeout(() => {
      btn.innerHTML = originalText;
    }, 2000);
    
  } catch (error) {
    console.error('Error downloading strong passwords:', error);
    showNotification('Không thể tải về file', 'error');
  }
}

function showNotification(message, type = 'info') {
  // Tạo notification element
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.textContent = message;
  
  // Style cho notification
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 20px;
    border-radius: 8px;
    color: white;
    font-weight: 600;
    z-index: 1000;
    transform: translateX(100%);
    transition: transform 0.3s ease;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  `;
  
  // Set màu dựa vào type
  switch(type) {
    case 'success':
      notification.style.background = 'linear-gradient(135deg, #34c759, #30d158)';
      break;
    case 'error':
      notification.style.background = 'linear-gradient(135deg, #ff3b30, #ff6b47)';
      break;
    default:
      notification.style.background = 'linear-gradient(135deg, #007AFF, #0051d5)';
  }
  
  document.body.appendChild(notification);
  
  // Animate in
  setTimeout(() => {
    notification.style.transform = 'translateX(0)';
  }, 10);
  
  // Remove after 3 seconds
  setTimeout(() => {
    notification.style.transform = 'translateX(100%)';
    setTimeout(() => {
      if (notification.parentNode) {
        document.body.removeChild(notification);
      }
    }, 300);
  }, 3000);
}

function updateStrongPasswordsSection(result) {
  const strongPasswordsBtn = document.getElementById('strong-passwords-btn');
  const strongPasswordsInfo = document.getElementById('strong-passwords-info');
  const strongCount = document.getElementById('strong-count');
  
  if (result.strong_passwords_list && result.strong_passwords_list.length > 0) {
    // Cập nhật dữ liệu global
    strongPasswordsData = {
      passwords: result.strong_passwords_list,
      filename: result.filename,
      count: result.strong_passwords_list.length
    };
    
    // Hiển thị button và info
    strongPasswordsBtn.style.display = 'inline-block';
    strongCount.textContent = `${strongPasswordsData.count} mật khẩu`;
    
    // Reset preview state
    const preview = document.getElementById('strong-passwords-preview');
    const previewBtn = document.getElementById('preview-strong-btn');
    preview.style.display = 'none';
    previewBtn.innerHTML = '👁️ Xem trước';
    strongPasswordsInfo.style.display = 'none';
  } else {
    // Ẩn button nếu không có mật khẩu mạnh
    strongPasswordsBtn.style.display = 'none';
    strongPasswordsInfo.style.display = 'none';
    strongPasswordsData = { passwords: [], filename: '', count: 0 };
  }
}

// Cập nhật hàm displayResult để bao gồm strong passwords
function displayResult(result, isSuccess) {
  if (currentMode === 'file') {
    window.lastFileResult = result;
    // Cập nhật section mật khẩu mạnh
    updateStrongPasswordsSection(result);
  } else {
    // Ẩn button cho single mode
    document.getElementById('strong-passwords-btn').style.display = 'none';
    document.getElementById('strong-passwords-info').style.display = 'none';
  }
  
  // Calculate check time
  const checkTime = checkStartTime ? 
    Math.round((Date.now() - checkStartTime) / 1000) : 0;
  document.getElementById('check-time').textContent = `${checkTime}s`;
  
  // Show result
  const resultElement = document.getElementById('result');
  const statusBadge = document.getElementById('status-badge');
  
  if (currentMode === 'single') {
    // Single password result
    let resultText = `🔐 KIỂM TRA MẬT KHẨU ĐƠN\n`;
    resultText += `${'='.repeat(40)}\n\n`;
    resultText += `Mật khẩu: ${result.password}\n\n`;
    resultText += `Trạng thái: ${result.is_strong ? '✅ Mạnh' : '❌ Yếu'}\n\n`;
    
    if (!result.is_strong && result.issues) {
      resultText += `🔍 Các vấn đề cần khắc phục:\n`;
      result.issues.forEach((issue, index) => {
        resultText += `  ${index + 1}. ${issue}\n`;
      });
      resultText += `\n💡 Khuyến nghị: Sửa các vấn đề trên để tăng độ bảo mật mật khẩu.`;
    } else {
      resultText += `✨ Mật khẩu của bạn đáp ứng các tiêu chuẩn bảo mật cơ bản!`;
    }
    
    resultElement.textContent = resultText;
    statusBadge.textContent = result.is_strong ? 'Mạnh' : 'Yếu';
    statusBadge.className = result.is_strong ? 'status-badge status-strong' : 'status-badge status-weak';
  } else {
    // File analysis result - Hiển thị đầy đủ như save_results_to_file
    let resultText = `📄 BÁO CÁO PHÂN TÍCH FILE MẬT KHẨU\n`;
    resultText += `Thời gian: ${result.timestamp}\n`;
    resultText += `File nguồn: ${result.filename}\n`;
    resultText += `${'='.repeat(50)}\n\n`;
    
    resultText += `📊 THỐNG KÊ TỔNG QUAN:\n`;
    resultText += `Tổng số mật khẩu: ${result.total_passwords}\n`;
    resultText += `Mật khẩu mạnh: ${result.strong_passwords} (${result.strong_percentage}%)\n`;
    resultText += `Mật khẩu yếu: ${result.weak_passwords} (${result.weak_percentage}%)\n\n`;
    
    // Thống kê chi tiết các vấn đề ở mật khẩu yếu
    resultText += `🔍 THỐNG KÊ CHI TIẾT CÁC VẤN ĐỀ Ở MẬT KHẨU YẾU:\n`;
    if (result.common_issues && result.common_issues.length > 0) {
      result.common_issues.forEach(issue => {
        resultText += `  - ${issue.issue}: ${issue.count} lần\n`;
      });
    } else {
      resultText += `  Không có vấn đề nào được ghi nhận.\n`;
    }
    resultText += `\n`;
    
    // Mẫu mật khẩu yếu (nếu có)
    if (result.sample_weak_passwords && result.sample_weak_passwords.length > 0) {
      resultText += `📝 MẪU MẬT KHẨU YẾU (${Math.min(10, result.sample_weak_passwords.length)} mẫu đầu tiên):\n`;
      result.sample_weak_passwords.slice(0, 10).forEach((pwd, index) => {
        resultText += `  ${index + 1}. ${pwd.password}\n`;
        resultText += `     Vấn đề: ${pwd.issues.join(', ')}\n`;
      });
      resultText += `\n💡 Khuyến nghị: Tránh sử dụng các mật khẩu có pattern tương tự.`;
    }
    
    resultElement.textContent = resultText;
    
    // Đặt status badge dựa trên tỷ lệ mật khẩu mạnh
    const strongPercent = result.strong_percentage;
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

// Thêm event listeners sau khi DOM loaded
document.addEventListener('DOMContentLoaded', function() {
  // Strong passwords button functionality
  const strongPasswordsBtn = document.getElementById('strong-passwords-btn');
  const previewStrongBtn = document.getElementById('preview-strong-btn');
  const downloadStrongBtn = document.getElementById('download-strong-btn');
  
  strongPasswordsBtn.addEventListener('click', toggleStrongPasswordsInfo);
  previewStrongBtn.addEventListener('click', toggleStrongPasswordsPreview);
  downloadStrongBtn.addEventListener('click', downloadStrongPasswords);
});

// Initialize default mode
switchMode('single');