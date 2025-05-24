const form = document.getElementById('strength-form');
const submitBtn = document.getElementById('submit-btn');
const cancelBtn = document.getElementById('cancel-btn');
const btnText = document.getElementById('btn-text');
const passwordInput = document.getElementById('password');
const fileInput = document.getElementById('password-file');
const togglePasswordBtn = document.getElementById('toggle-password');
const modeButtons = document.querySelectorAll('.mode-btn');
const modeInfos = document.querySelectorAll('.mode-info');

// Elements cho compare mode
const model1NameInput = document.getElementById('model1-name');
const model1FileInput = document.getElementById('model1-file');
const model2NameInput = document.getElementById('model2-name');
const model2FileInput = document.getElementById('model2-file');
const model3NameInput = document.getElementById('model3-name');
const model3FileInput = document.getElementById('model3-file');

let currentMode = 'single';
let checkStartTime = null;
let isProcessing = false;
let currentController = null;

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
  const compareForm = document.querySelector('.compare-mode-form');
  
  // Hide all forms first
  if (singleForm) singleForm.style.display = 'none';
  if (fileForm) fileForm.style.display = 'none';
  if (compareForm) compareForm.style.display = 'none';
  
  // Reset required attributes
  if (passwordInput) passwordInput.required = false;
  if (fileInput) fileInput.required = false;
  if (model1FileInput) model1FileInput.required = false;
  if (model2FileInput) model2FileInput.required = false;
  
  if (mode === 'single') {
    if (singleForm) singleForm.style.display = 'block';
    if (passwordInput) passwordInput.required = true;
    btnText.textContent = 'Kiểm tra độ mạnh';
  } else if (mode === 'file') {
    if (fileForm) fileForm.style.display = 'block';
    if (fileInput) fileInput.required = true;
    btnText.textContent = 'Phân tích file';
  } else if (mode === 'compare') {
    if (compareForm) compareForm.style.display = 'block';
    if (model1FileInput) model1FileInput.required = true;
    if (model2FileInput) model2FileInput.required = true;
    btnText.textContent = 'So sánh model';
  }
}

// Password toggle functionality
if (togglePasswordBtn) {
  togglePasswordBtn.addEventListener('click', () => {
    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordInput.setAttribute('type', type);
    togglePasswordBtn.textContent = type === 'password' ? '👁️ Hiện' : '🙈 Ẩn';
  });
}

// Cancel button functionality
if (cancelBtn) {
  cancelBtn.addEventListener('click', async () => {
    if (!isProcessing) return;
    
    try {
      if (currentController) {
        currentController.abort();
      }
      
      resetToInitialState();
      
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
}

function showResult() {
  document.getElementById('result-placeholder').classList.add('hidden');
  document.getElementById('result-content').classList.add('show');
  
  document.querySelector('.container').classList.add('has-result');
  
  // Update mode indicator
  const modeIndicator = document.getElementById('mode-indicator');
  let modeIcon, modeText;
  
  switch(currentMode) {
    case 'single':
      modeIcon = '🔒';
      modeText = 'Đơn';
      break;
    case 'file':
      modeIcon = '📄';
      modeText = 'File';
      break;
    case 'compare':
      modeIcon = '⚖️';
      modeText = 'So sánh';
      break;
    default:
      modeIcon = '🔒';
      modeText = 'Đơn';
  }
  
  modeIndicator.textContent = `${modeIcon} ${modeText}`;
}

function setProcessingState(processing) {
  isProcessing = processing;
  
  if (processing) {
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;
    if (cancelBtn) cancelBtn.classList.add('show');
    
    switch(currentMode) {
      case 'single':
        btnText.textContent = 'Đang kiểm tra...';
        break;
      case 'file':
        btnText.textContent = 'Đang phân tích...';
        break;
      case 'compare':
        btnText.textContent = 'Đang so sánh...';
        break;
    }
  } else {
    submitBtn.classList.remove('loading');
    submitBtn.disabled = false;
    if (cancelBtn) cancelBtn.classList.remove('show');
    
    switch(currentMode) {
      case 'single':
        btnText.textContent = 'Kiểm tra độ mạnh';
        break;
      case 'file':
        btnText.textContent = 'Phân tích file';
        break;
      case 'compare':
        btnText.textContent = 'So sánh model';
        break;
    }
  }
}

function resetToInitialState() {
  setProcessingState(false);
  checkStartTime = null;
  currentController = null;
}

// Main form submission handler
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  
  if (isProcessing) return;
  
  checkStartTime = Date.now();
  setProcessingState(true);
  
  currentController = new AbortController();

  try {
    let endpoint = '';
    let requestOptions = {
      method: 'POST',
      signal: currentController.signal
    };
    
    if (currentMode === 'single') {
      if (!passwordInput.value.trim()) {
        throw new Error('Vui lòng nhập mật khẩu');
      }
      
      const data = { password: passwordInput.value };
      endpoint = '/check_single_password';
      requestOptions.headers = {'Content-Type': 'application/json'};
      requestOptions.body = JSON.stringify(data);
      
    } else if (currentMode === 'file') {
      if (!fileInput.files[0]) {
        throw new Error('Vui lòng chọn file để phân tích');
      }
      
      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
      endpoint = '/check_password_file';
      requestOptions.body = formData;
      
    } else if (currentMode === 'compare') {
      if (!model1FileInput.files[0] || !model2FileInput.files[0]) {
        throw new Error('Vui lòng chọn ít nhất 2 file để so sánh');
      }
      
      const formData = new FormData();
      formData.append('model1_file', model1FileInput.files[0]);
      formData.append('model1_name', model1NameInput.value || 'Model 1');
      formData.append('model2_file', model2FileInput.files[0]);
      formData.append('model2_name', model2NameInput.value || 'Model 2');
      
      if (model3FileInput.files[0]) {
        formData.append('model3_file', model3FileInput.files[0]);
        formData.append('model3_name', model3NameInput.value || 'Model 3');
      }
      
      endpoint = '/compare_password_strength';
      requestOptions.body = formData;
    }

    console.log('Sending request to:', endpoint, 'Mode:', currentMode);

    const res = await fetch(endpoint, requestOptions);
    
    if (!res.ok) {
      const errorText = await res.text();
      console.error('Response error:', res.status, errorText);
      throw new Error(`HTTP Error: ${res.status} - ${errorText}`);
    }
    
    const result = await res.json();
    console.log('Received result:', result);
    
    if (result.error) {
      throw new Error(result.error);
    }
    
    displayResult(result, true);

  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('Request was cancelled');
      return;
    }
    
    console.error('Strength analysis error:', error);
    
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
  const checkTime = checkStartTime ? 
    Math.round((Date.now() - checkStartTime) / 1000) : 0;
  document.getElementById('check-time').textContent = `${checkTime}s`;
  
  const resultElement = document.getElementById('result');
  const statusBadge = document.getElementById('status-badge');
  const chartBtn = document.getElementById('chart-btn');
  const chartImage = document.getElementById('chart-image');
  const chartContainer = document.getElementById('chart-container');
  
  // Handle chart display
  if (result.chart) {
    console.log('Chart data found, displaying chart...');
    
    // Ensure chart button exists and is visible
    if (chartBtn) {
      chartBtn.style.display = 'inline-block';
    }
    
    // Set chart image
    if (chartImage) {
      chartImage.src = `data:image/png;base64,${result.chart}`;
      console.log('Chart image src set');
    }
    
    // Auto show chart for compare mode
    if (currentMode === 'compare' && chartContainer) {
      setTimeout(() => {
        chartContainer.style.display = 'block';
        if (chartBtn) chartBtn.innerHTML = '📊 Ẩn biểu đồ';
        console.log('Chart container displayed');
      }, 500);
    }
  } else {
    console.log('No chart data found');
    if (chartBtn) chartBtn.style.display = 'none';
    if (chartContainer) chartContainer.style.display = 'none';
  }
  
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
    
    // Hide strong passwords section for single mode
    const strongPasswordsBtn = document.getElementById('strong-passwords-btn');
    const strongPasswordsInfo = document.getElementById('strong-passwords-info');
    if (strongPasswordsBtn) strongPasswordsBtn.style.display = 'none';
    if (strongPasswordsInfo) strongPasswordsInfo.style.display = 'none';
    
  } else if (currentMode === 'file') {
    // File analysis result
    updateStrongPasswordsSection(result);
    
    let resultText = `📄 BÁO CÁO PHÂN TÍCH FILE MẬT KHẨU\n`;
    resultText += `Thời gian: ${result.timestamp}\n`;
    resultText += `File nguồn: ${result.filename}\n`;
    resultText += `${'='.repeat(50)}\n\n`;
    
    resultText += `📊 THỐNG KÊ TỔNG QUAN:\n`;
    resultText += `Tổng số mật khẩu: ${result.total_passwords}\n`;
    resultText += `Mật khẩu mạnh: ${result.strong_passwords} (${result.strong_percentage}%)\n`;
    resultText += `Mật khẩu yếu: ${result.weak_passwords} (${result.weak_percentage}%)\n\n`;
    
    // Thống kê chi tiết các vấn đề
    resultText += `🔍 THỐNG KÊ CHI TIẾT CÁC VẤN ĐỀ:\n`;
    if (result.common_issues && result.common_issues.length > 0) {
      result.common_issues.forEach(issue => {
        resultText += `  - ${issue.issue}: ${issue.count} lần\n`;
      });
    } else {
      resultText += `  Không có vấn đề nào được ghi nhận.\n`;
    }
    
    resultElement.textContent = resultText;
    
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
    
  } else if (currentMode === 'compare') {
    // Comparison result
    let resultText = `⚖️ BÁO CÁO SO SÁNH MODEL\n`;
    resultText += `Thời gian: ${result.timestamp}\n`;
    resultText += `Số model so sánh: ${result.total_models}\n`;
    resultText += `${'='.repeat(50)}\n\n`;
    
    resultText += `🏆 BẢNG XẾP HẠNG:\n`;
    result.models.forEach((model, index) => {
      const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`;
      resultText += `${medal} ${model.model_name}: ${model.strong_percentage}% mật khẩu mạnh\n`;
      resultText += `   Tổng: ${model.total_passwords.toLocaleString()} | Mạnh: ${model.strong_count.toLocaleString()} | Yếu: ${model.weak_count.toLocaleString()}\n\n`;
    });
    
    // Chi tiết từng model
    resultText += `📊 CHI TIẾT TỪNG MODEL:\n`;
    result.models.forEach(model => {
      resultText += `\n▶️ ${model.model_name}:\n`;
      resultText += `  📈 Tỷ lệ mạnh: ${model.strong_percentage}%\n`;
      resultText += `  📏 Độ dài TB (mạnh): ${model.avg_strong_length} ký tự\n`;
      resultText += `  📏 Độ dài TB (tổng): ${model.avg_total_length} ký tự\n`;
      resultText += `  🔤 Ký tự hoa TB: ${model.strong_char_stats.avg_uppercase}\n`;
      resultText += `  🔡 Ký tự thường TB: ${model.strong_char_stats.avg_lowercase}\n`;
      resultText += `  🔢 Chữ số TB: ${model.strong_char_stats.avg_digits}\n`;
      resultText += `  🔣 Ký tự đặc biệt TB: ${model.strong_char_stats.avg_special}\n`;
    });
    
    // Thông báo về biểu đồ
    if (result.chart) {
      resultText += `\n📊 BIỂU ĐỒ SO SÁNH:\n`;
      resultText += `✅ Biểu đồ chi tiết đã được tạo - nhấn nút "📊 Biểu đồ" để xem\n`;
      resultText += `   • Strong password percentage comparison\n`;
      resultText += `   • Total password count comparison\n`;
      resultText += `   • Password length analysis\n`;
      resultText += `   • Character distribution comparison\n`;
    }
    
    resultElement.textContent = resultText;
    
    // Set status based on best model performance
    const bestPercentage = result.best_model ? result.best_model.strong_percentage : 0;
    if (bestPercentage >= 70) {
      statusBadge.textContent = 'Xuất sắc';
      statusBadge.className = 'status-badge status-strong';
    } else if (bestPercentage >= 50) {
      statusBadge.textContent = 'Tốt';
      statusBadge.className = 'status-badge status-weak';
    } else {
      statusBadge.textContent = 'Cần cải thiện';
      statusBadge.className = 'status-badge status-error';
    }
    
    // Hide strong passwords section for compare mode
    const strongPasswordsBtn = document.getElementById('strong-passwords-btn');
    const strongPasswordsInfo = document.getElementById('strong-passwords-info');
    if (strongPasswordsBtn) strongPasswordsBtn.style.display = 'none';
    if (strongPasswordsInfo) strongPasswordsInfo.style.display = 'none';
  }
  
  showResult();
}

// Chart functionality
function toggleChart() {
  const chartContainer = document.getElementById('chart-container');
  const chartBtn = document.getElementById('chart-btn');
  
  if (!chartContainer || !chartBtn) return;
  
  if (chartContainer.style.display === 'none') {
    chartContainer.style.display = 'block';
    chartBtn.innerHTML = '📊 Ẩn biểu đồ';
  } else {
    hideChart();
  }
}

function hideChart() {
  const chartContainer = document.getElementById('chart-container');
  const chartBtn = document.getElementById('chart-btn');
  
  if (!chartContainer || !chartBtn) return;
  
  chartContainer.classList.add('hiding');
  setTimeout(() => {
    chartContainer.style.display = 'none';
    chartContainer.classList.remove('hiding');
    chartBtn.innerHTML = '📊 Biểu đồ';
  }, 300);
}

// Strong passwords functionality
function updateStrongPasswordsSection(result) {
  const strongPasswordsBtn = document.getElementById('strong-passwords-btn');
  const strongPasswordsInfo = document.getElementById('strong-passwords-info');
  const strongCount = document.getElementById('strong-count');
  
  if (!strongPasswordsBtn || !strongPasswordsInfo || !strongCount) return;
  
  if (result.strong_passwords_list && result.strong_passwords_list.length > 0) {
    strongPasswordsData = {
      passwords: result.strong_passwords_list,
      filename: result.filename,
      count: result.strong_passwords_list.length
    };
    
    strongPasswordsBtn.style.display = 'inline-block';
    strongCount.textContent = `${strongPasswordsData.count} mật khẩu`;
    
    const preview = document.getElementById('strong-passwords-preview');
    const previewBtn = document.getElementById('preview-strong-btn');
    if (preview) preview.style.display = 'none';
    if (previewBtn) previewBtn.innerHTML = '👁️ Xem trước';
    strongPasswordsInfo.style.display = 'none';
  } else {
    strongPasswordsBtn.style.display = 'none';
    strongPasswordsInfo.style.display = 'none';
    strongPasswordsData = { passwords: [], filename: '', count: 0 };
  }
}

function toggleStrongPasswordsInfo() {
  const info = document.getElementById('strong-passwords-info');
  if (!info) return;
  
  if (info.style.display === 'none') {
    info.style.display = 'block';
  } else {
    info.style.display = 'none';
  }
}

function toggleStrongPasswordsPreview() {
  const preview = document.getElementById('strong-passwords-preview');
  const btn = document.getElementById('preview-strong-btn');
  
  if (!preview || !btn) return;
  
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
  if (!listContainer) return;
  
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
    
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `strong_passwords_${Date.now()}.txt`;
    a.style.display = 'none';
    
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showNotification(`Đã tải về ${strongPasswordsData.count} mật khẩu mạnh!`, 'success');
    
    const btn = document.getElementById('download-strong-btn');
    if (btn) {
      const originalText = btn.innerHTML;
      btn.innerHTML = '✅ Đã tải về!';
      setTimeout(() => {
        btn.innerHTML = originalText;
      }, 2000);
    }
    
  } catch (error) {
    console.error('Error downloading strong passwords:', error);
    showNotification('Không thể tải về file', 'error');
  }
}

function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.textContent = message;
  
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
  
  setTimeout(() => {
    notification.style.transform = 'translateX(0)';
  }, 10);
  
  setTimeout(() => {
    notification.style.transform = 'translateX(100%)';
    setTimeout(() => {
      if (notification.parentNode) {
        document.body.removeChild(notification);
      }
    }, 300);
  }, 3000);
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

// Initialize event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Strong passwords button functionality
  const strongPasswordsBtn = document.getElementById('strong-passwords-btn');
  const previewStrongBtn = document.getElementById('preview-strong-btn');
  const downloadStrongBtn = document.getElementById('download-strong-btn');
  
  if (strongPasswordsBtn) strongPasswordsBtn.addEventListener('click', toggleStrongPasswordsInfo);
  if (previewStrongBtn) previewStrongBtn.addEventListener('click', toggleStrongPasswordsPreview);
  if (downloadStrongBtn) downloadStrongBtn.addEventListener('click', downloadStrongPasswords);
  
  // Chart functionality
  const chartBtn = document.getElementById('chart-btn');
  const chartToggleBtn = document.getElementById('chart-toggle-btn');
  
  if (chartBtn) chartBtn.addEventListener('click', toggleChart);
  if (chartToggleBtn) chartToggleBtn.addEventListener('click', hideChart);
});

// Initialize default mode
switchMode('single');