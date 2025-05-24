/* Pattern Checker JavaScript */
const form = document.getElementById('pattern-form');
const submitBtn = document.getElementById('submit-btn');
const cancelBtn = document.getElementById('cancel-btn');
const btnText = document.getElementById('btn-text');
const modeButtons = document.querySelectorAll('.mode-btn');
const modeInfos = document.querySelectorAll('.mode-info');

// File inputs
const plaintextFileInput = document.getElementById('plaintext-file');
const dcFileInput = document.getElementById('dc-file');
const passgptFileInput = document.getElementById('passgpt-file');
const passganFileInput = document.getElementById('passgan-file');
const analyzeFileInput = document.getElementById('analyze-file');

let currentMode = 'compare';
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
  const compareForm = document.querySelector('.compare-mode-form');
  const analyzeForm = document.querySelector('.analyze-mode-form');
  
  if (mode === 'compare') {
    compareForm.style.display = 'block';
    analyzeForm.style.display = 'none';
    
    // Set required attributes
    plaintextFileInput.required = true;
    dcFileInput.required = true;
    passgptFileInput.required = true;
    passganFileInput.required = true;
    analyzeFileInput.required = false;
    
    btnText.textContent = 'So sánh Pattern';
  } else {
    compareForm.style.display = 'none';
    analyzeForm.style.display = 'block';
    
    // Set required attributes
    plaintextFileInput.required = false;
    dcFileInput.required = false;
    passgptFileInput.required = false;
    passganFileInput.required = false;
    analyzeFileInput.required = true;
    
    btnText.textContent = 'Phân tích Pattern';
  }
}

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
    
    resultElement.textContent = `❌ Quá trình phân tích đã bị hủy bởi người dùng\n\nThời gian hủy: ${new Date().toLocaleString()}`;
    statusBadge.textContent = 'Đã hủy';
    statusBadge.className = 'status-badge status-poor';
    
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
  const modeIcon = currentMode === 'compare' ? '📊' : '🔍';
  const modeText = currentMode === 'compare' ? 'So sánh' : 'Phân tích';
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
    btnText.textContent = currentMode === 'compare' ? 'Đang so sánh...' : 'Đang phân tích...';
  } else {
    // Reset button state
    submitBtn.classList.remove('loading');
    submitBtn.disabled = false;
    cancelBtn.classList.remove('show');
    const modeText = currentMode === 'compare' ? 'So sánh Pattern' : 'Phân tích Pattern';
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
    const formData = new FormData();
    let endpoint = '';
    
    if (currentMode === 'compare') {
      // Compare mode - 4 files
      if (!plaintextFileInput.files[0] || !dcFileInput.files[0] || 
          !passgptFileInput.files[0] || !passganFileInput.files[0]) {
        throw new Error('Vui lòng chọn đầy đủ 4 file để so sánh');
      }
      
      formData.append('plaintext_file', plaintextFileInput.files[0]);
      formData.append('dc_file', dcFileInput.files[0]);
      formData.append('passgpt_file', passgptFileInput.files[0]);
      formData.append('passgan_file', passganFileInput.files[0]);
      endpoint = '/compare_password_patterns';
    } else {
      // Analyze mode - 1 file
      if (!analyzeFileInput.files[0]) {
        throw new Error('Vui lòng chọn file để phân tích');
      }
      
      formData.append('password_file', analyzeFileInput.files[0]);
      endpoint = '/analyze_password_patterns';
    }

    const res = await fetch(endpoint, {
      method: 'POST',
      signal: currentController.signal,
      body: formData
    });
    
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
    document.getElementById('status-badge').className = 'status-badge status-poor';
    showResult();
  } finally {
    setProcessingState(false);
    currentController = null;
  }
});

function displayResult(result, isSuccess) {
  if (currentMode === 'compare') {
    window.lastCompareResult = result;
  } else {
    window.lastAnalyzeResult = result;
  }
  
  // Calculate check time
  const checkTime = checkStartTime ? 
    Math.round((Date.now() - checkStartTime) / 1000) : 0;
  document.getElementById('check-time').textContent = `${checkTime}s`;
  
  // Show result
  const resultElement = document.getElementById('result');
  const statusBadge = document.getElementById('status-badge');
  
  if (currentMode === 'compare') {
    // Compare mode result
    let resultText = `📊 BÁO CÁO SO SÁNH PATTERN MẬT KHẨU\n`;
    resultText += `Thời gian: ${result.timestamp}\n`;
    resultText += `${'='.repeat(60)}\n\n`;
    
    // Thêm biểu đồ nếu có
    if (result.chart) {
      resultText += `📈 BIỂU ĐỒ SO SÁNH:\n`;
      resultText += `[Biểu đồ được hiển thị bên dưới]\n\n`;
    }
    
    resultText += `📈 PHÂN TÍCH LENGTH DISTRIBUTION:\n`;
    resultText += `Length Distance (so với plaintext gốc):\n`;
    result.length_distances.forEach((item, index) => {
      const models = ['DC Generated', 'PassGPT', 'PassGAN'];
      resultText += `  • ${models[index]}: ${item.distance.toFixed(6)}\n`;
    });
    resultText += `\n`;
    
    resultText += `🧩 PHÂN TÍCH PATTERN DISTRIBUTION:\n`;
    resultText += `Pattern Distance (so với plaintext gốc):\n`;
    result.pattern_distances.forEach((item, index) => {
      const models = ['DC Generated', 'PassGPT', 'PassGAN'];
      resultText += `  • ${models[index]}: ${item.distance.toFixed(6)}\n`;
    });
    resultText += `\n`;
    
    resultText += `🏆 XẾP HẠNG MODEL:\n`;
    
    // Tính điểm tổng hợp (distance càng thấp càng tốt)
    const totalScores = result.length_distances.map((_, index) => ({
      model: ['DC Generated', 'PassGPT', 'PassGAN'][index],
      lengthDist: result.length_distances[index].distance,
      patternDist: result.pattern_distances[index].distance,
      totalScore: result.length_distances[index].distance + result.pattern_distances[index].distance
    }));
    
    totalScores.sort((a, b) => a.totalScore - b.totalScore);
    
    totalScores.forEach((item, index) => {
      const rank = index + 1;
      const medal = rank === 1 ? '🥇' : rank === 2 ? '🥈' : '🥉';
      resultText += `  ${medal} ${rank}. ${item.model}\n`;
      resultText += `     Length Distance: ${item.lengthDist.toFixed(6)}\n`;
      resultText += `     Pattern Distance: ${item.patternDist.toFixed(6)}\n`;
      resultText += `     Tổng điểm: ${item.totalScore.toFixed(6)}\n\n`;
    });
    
    resultText += `📊 THỐNG KÊ FILE:\n`;
    resultText += `  • Mật khẩu gốc: ${result.stats.original_passwords.toLocaleString()}\n`;
    resultText += `  • DC Generated: ${result.stats.dc_passwords.toLocaleString()}\n`;
    resultText += `  • PassGPT: ${result.stats.passgpt_passwords.toLocaleString()}\n`;
    resultText += `  • PassGAN: ${result.stats.passgan_passwords.toLocaleString()}\n\n`;
    
    resultText += `💡 NHẬN XÉT:\n`;
    const bestModel = totalScores[0];
    const worstModel = totalScores[2];
    
    resultText += `  • Model tốt nhất: ${bestModel.model} (điểm: ${bestModel.totalScore.toFixed(6)})\n`;
    resultText += `  • Model cần cải thiện: ${worstModel.model} (điểm: ${worstModel.totalScore.toFixed(6)})\n`;
    
    if (bestModel.totalScore < 0.1) {
      resultText += `  • ${bestModel.model} có pattern rất giống plaintext gốc\n`;
    } else if (bestModel.totalScore < 0.3) {
      resultText += `  • ${bestModel.model} có pattern khá giống plaintext gốc\n`;
    } else {
      resultText += `  • Tất cả model đều có pattern khác biệt đáng kể so với plaintext gốc\n`;
    }
    
    resultElement.textContent = resultText;
    
    // Hiển thị biểu đồ
    if (result.chart) {
      addChartToResult(result.chart, 'Biểu đồ so sánh Pattern Analysis');
    }
    
    // Set status based on best model performance
    if (bestModel.totalScore < 0.1) {
      statusBadge.textContent = 'Xuất sắc';
      statusBadge.className = 'status-badge status-excellent';
    } else if (bestModel.totalScore < 0.3) {
      statusBadge.textContent = 'Tốt';
      statusBadge.className = 'status-badge status-good';
    } else if (bestModel.totalScore < 0.5) {
      statusBadge.textContent = 'Trung bình';
      statusBadge.className = 'status-badge status-average';
    } else {
      statusBadge.textContent = 'Cần cải thiện';
      statusBadge.className = 'status-badge status-poor';
    }
    
  } else {
    // Analyze mode result
    let resultText = `🔍 BÁO CÁO PHÂN TÍCH PATTERN MẬT KHẨU\n`;
    resultText += `Thời gian: ${result.timestamp}\n`;
    resultText += `File: ${result.filename}\n`;
    resultText += `${'='.repeat(50)}\n\n`;
    
    // Thêm biểu đồ nếu có
    if (result.chart) {
      resultText += `📊 BIỂU ĐỒ PHÂN TÍCH:\n`;
      resultText += `[Biểu đồ được hiển thị bên dưới]\n\n`;
    }
    
    resultText += `📊 THỐNG KÊ TỔNG QUAN:\n`;
    resultText += `Tổng số mật khẩu: ${result.total_passwords.toLocaleString()}\n`;
    resultText += `Độ dài trung bình: ${result.avg_length.toFixed(2)} ký tự\n`;
    resultText += `Số pattern duy nhất: ${result.unique_patterns.toLocaleString()}\n\n`;
    
    resultText += `📏 PHÂN PHỐI ĐỘ DÀI (Top 10):\n`;
    result.top_lengths.forEach((item, index) => {
      const percentage = (item.frequency * 100).toFixed(2);
      resultText += `  ${index + 1}. Độ dài ${item.length}: ${item.count.toLocaleString()} (${percentage}%)\n`;
    });
    resultText += `\n`;
    
    resultText += `🧩 PHÂN PHỐI PATTERN (Top 15):\n`;
    result.top_patterns.forEach((item, index) => {
      const percentage = (item.frequency * 100).toFixed(2);
      resultText += `  ${index + 1}. ${item.pattern}: ${item.count.toLocaleString()} (${percentage}%)\n`;
    });
    resultText += `\n`;
    
    resultText += `📋 GIẢI THÍCH PATTERN:\n`;
    resultText += `  L = Chữ thường (lowercase)\n`;
    resultText += `  U = Chữ hoa (uppercase)\n`;
    resultText += `  D = Chữ số (digit)\n`;
    resultText += `  S = Ký tự đặc biệt (special)\n\n`;
    
    resultText += `💡 PHÂN TÍCH:\n`;
    const topPattern = result.top_patterns[0];
    resultText += `  • Pattern phổ biến nhất: ${topPattern.pattern} (${(topPattern.frequency * 100).toFixed(2)}%)\n`;
    
    const diversity = result.unique_patterns / result.total_passwords;
    if (diversity > 0.8) {
      resultText += `  • Độ đa dạng pattern: Rất cao (${(diversity * 100).toFixed(1)}%)\n`;
    } else if (diversity > 0.5) {
      resultText += `  • Độ đa dạng pattern: Cao (${(diversity * 100).toFixed(1)}%)\n`;
    } else if (diversity > 0.3) {
      resultText += `  • Độ đa dạng pattern: Trung bình (${(diversity * 100).toFixed(1)}%)\n`;
    } else {
      resultText += `  • Độ đa dạng pattern: Thấp (${(diversity * 100).toFixed(1)}%)\n`;
    }
    
    resultElement.textContent = resultText;
    
    // Hiển thị biểu đồ
    if (result.chart) {
      addChartToResult(result.chart, `Biểu đồ phân tích Pattern - ${result.filename}`);
    }
    
    // Set status based on pattern diversity
    if (diversity > 0.8) {
      statusBadge.textContent = 'Xuất sắc';
      statusBadge.className = 'status-badge status-excellent';
    } else if (diversity > 0.5) {
      statusBadge.textContent = 'Tốt';
      statusBadge.className = 'status-badge status-good';
    } else if (diversity > 0.3) {
      statusBadge.textContent = 'Trung bình';
      statusBadge.className = 'status-badge status-average';
    } else {
      statusBadge.textContent = 'Cần cải thiện';
      statusBadge.className = 'status-badge status-poor';
    }
  }
  
  showResult();
}

function addChartToResult(chartBase64, title) {
  // Remove existing chart if any
  const existingChart = document.getElementById('pattern-chart');
  if (existingChart) {
    existingChart.remove();
  }
  
  // Create chart container
  const chartContainer = document.createElement('div');
  chartContainer.id = 'pattern-chart';
  chartContainer.style.cssText = `
    margin: 20px 0;
    text-align: center;
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    border: 1px solid #e5e5e7;
  `;
  
  // Create title
  const chartTitle = document.createElement('h4');
  chartTitle.textContent = title;
  chartTitle.style.cssText = `
    margin: 0 0 16px 0;
    color: #1d1d1f;
    font-size: 16px;
    font-weight: 600;
  `;
  
  // Create image element
  const chartImg = document.createElement('img');
  chartImg.src = `data:image/png;base64,${chartBase64}`;
  chartImg.style.cssText = `
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  `;
  
  // Add download button for chart
  const downloadChartBtn = document.createElement('button');
  downloadChartBtn.textContent = '💾 Download Biểu đồ';
  downloadChartBtn.style.cssText = `
    margin-top: 12px;
    padding: 8px 16px;
    background: linear-gradient(135deg, #ff9500, #ff6b47);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  `;
  
  downloadChartBtn.addEventListener('click', () => {
    const link = document.createElement('a');
    link.href = chartImg.src;
    link.download = `pattern-chart-${currentMode}-${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    const originalText = downloadChartBtn.textContent;
    downloadChartBtn.textContent = '✅ Downloaded!';
    setTimeout(() => {
      downloadChartBtn.textContent = originalText;
    }, 2000);
  });
  
  downloadChartBtn.addEventListener('mouseenter', () => {
    downloadChartBtn.style.transform = 'translateY(-2px)';
    downloadChartBtn.style.boxShadow = '0 4px 12px rgba(255, 149, 0, 0.3)';
  });
  
  downloadChartBtn.addEventListener('mouseleave', () => {
    downloadChartBtn.style.transform = 'translateY(0)';
    downloadChartBtn.style.boxShadow = 'none';
  });
  
  // Assemble chart container
  chartContainer.appendChild(chartTitle);
  chartContainer.appendChild(chartImg);
  chartContainer.appendChild(downloadChartBtn);
  
  // Insert chart after result text
  const resultElement = document.getElementById('result');
  resultElement.parentNode.insertBefore(chartContainer, resultElement.nextSibling);
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
    a.download = `pattern-analysis-${currentMode}-${Date.now()}.txt`;
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
switchMode('compare');