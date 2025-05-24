const form = document.getElementById('gen-form');
const submitBtn = document.getElementById('submit-btn');
const cancelBtn = document.getElementById('cancel-btn');
const btnText = document.getElementById('btn-text');
const resultSection = document.getElementById('result-section');
const statusBadge = document.getElementById('status-badge');
const resultElement = document.getElementById('result');
const modeButtons = document.querySelectorAll('.mode-btn');
const modeInfos = document.querySelectorAll('.mode-info');

let currentController = null;
let statusCheckInterval = null;
let currentMode = 'normal'; // Default mode
let executionStartTime = null;

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
  
  // Update button text
  const modeText = mode === 'normal' ? 'Normal' : 'DC';
  btnText.textContent = `Bắt đầu tạo dữ liệu (${modeText})`;
}

function showResult() {
  document.getElementById('result-placeholder').classList.add('hidden');
  document.getElementById('result-content').classList.add('show');
  
  // Expand container for better PC experience
  document.querySelector('.container').classList.add('has-result');
  
  // Update mode indicator
  const modeIndicator = document.getElementById('mode-indicator');
  const modeIcon = currentMode === 'normal' ? '🚀' : '🧠';
  const modeText = currentMode === 'normal' ? 'Normal' : 'DC';
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
  
  currentController = new AbortController();
  executionStartTime = Date.now();
  
  // Show loading state
  submitBtn.classList.add('loading');
  btnText.textContent = `Đang xử lý (${currentMode.toUpperCase()})...`;
  submitBtn.disabled = true;
  cancelBtn.classList.add('show');

  startStatusCheck();

  try {
    const data = {
      output_path: document.getElementById('output_path').value,
      generate_num: parseInt(document.getElementById('generate_num').value),
      batch_size: parseInt(document.getElementById('batch_size').value),
      gpu_num: parseInt(document.getElementById('gpu_num').value),
      gpu_index: parseInt(document.getElementById('gpu_index').value)
    };

    // Add cleaned_dataset for DC mode (hardcoded)
    if (currentMode === 'dc') {
      data.cleaned_dataset = 'dataset/rockyou-cleaned.txt';
    }

    // Choose endpoint based on mode
    const endpoint = currentMode === 'normal' ? '/normal_generate' : '/dc_generate';

    const res = await fetch(endpoint, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data),
      signal: currentController.signal
    });

    const result = await res.json();
    
    // Calculate execution time
    const executionTime = executionStartTime ? 
      Math.round((Date.now() - executionStartTime) / 1000) : 0;
    document.getElementById('execution-time').textContent = `${executionTime}s`;
    
    // Show result
    resultElement.textContent = JSON.stringify(result, null, 2);
    resultElement.classList.add('json-content');
    showResult();
    
    // Update status badge
    if (res.ok) {
      statusBadge.textContent = 'Thành công';
      statusBadge.className = 'status-badge status-success';
    } else {
      statusBadge.textContent = 'Lỗi';
      statusBadge.className = 'status-badge status-error';
    }

  } catch (error) {
    const executionTime = executionStartTime ? 
      Math.round((Date.now() - executionStartTime) / 1000) : 0;
    document.getElementById('execution-time').textContent = `${executionTime}s`;
    
    if (error.name === 'AbortError') {
      resultElement.textContent = 'Quá trình tạo dữ liệu đã bị hủy.';
      statusBadge.textContent = 'Đã hủy';
      statusBadge.className = 'status-badge status-error';
    } else {
      resultElement.textContent = `Lỗi: ${error.message}`;
      statusBadge.textContent = 'Lỗi';
      statusBadge.className = 'status-badge status-error';
    }
    resultElement.classList.remove('json-content');
    showResult();
  } finally {
    stopStatusCheck();
    resetButtonState();
    executionStartTime = null;
  }
});

// Cancel button handler
cancelBtn.addEventListener('click', async () => {
  try {
    btnText.textContent = 'Đang hủy...';
    cancelBtn.disabled = true;
    
    if (currentController) {
      currentController.abort();
    }
    
    const response = await fetch('/cancel_generation', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'}
    });
    
    const result = await response.json();
    console.log('Cancel response:', result);
    
    if (result.success) {
      resultElement.textContent = `Đã hủy ${result.cancelled_count} processes thành công.`;
      statusBadge.textContent = 'Đã hủy';
      statusBadge.className = 'status-badge status-error';
      showResult();
    }
    
  } catch (err) {
    console.log('Cancel request failed:', err);
    resultElement.textContent = 'Lỗi khi hủy process.';
    statusBadge.textContent = 'Lỗi hủy';
    statusBadge.className = 'status-badge status-error';
    showResult();
  } finally {
    cancelBtn.disabled = false;
  }
});

function startStatusCheck() {
  statusCheckInterval = setInterval(async () => {
    try {
      const response = await fetch('/status');
      const status = await response.json();
      
      if (status.running_processes > 0) {
        btnText.textContent = `Đang xử lý (${currentMode.toUpperCase()})... (${status.running_processes} processes)`;
      } else {
        btnText.textContent = `Đang xử lý (${currentMode.toUpperCase()})...`;
      }
    } catch (err) {
      console.log('Status check failed:', err);
    }
  }, 2000);
}

function stopStatusCheck() {
  if (statusCheckInterval) {
    clearInterval(statusCheckInterval);
    statusCheckInterval = null;
  }
}

function resetButtonState() {
  submitBtn.classList.remove('loading');
  const modeText = currentMode === 'normal' ? 'Normal' : 'DC';
  btnText.textContent = `Bắt đầu tạo dữ liệu (${modeText})`;
  submitBtn.disabled = false;
  cancelBtn.classList.remove('show');
  cancelBtn.disabled = false;
  currentController = null;
}

// Input validation
const inputs = document.querySelectorAll('input[required]');
inputs.forEach(input => {
  input.addEventListener('invalid', function() {
    this.style.borderColor = '#ff3b30';
    this.style.boxShadow = '0 0 0 4px rgba(255, 59, 48, 0.1)';
  });
  
  input.addEventListener('input', function() {
    if (this.validity.valid) {
      this.style.borderColor = '#007AFF';
      this.style.boxShadow = '0 0 0 4px rgba(0, 122, 255, 0.1)';
    }
  });
});

// Copy button functionality
document.getElementById('copy-btn').addEventListener('click', async () => {
  try {
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
    const content = resultElement.textContent;
    const blob = new Blob([content], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ppgt-result-${currentMode}-${Date.now()}.json`;
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
switchMode('normal');