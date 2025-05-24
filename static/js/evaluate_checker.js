/* filepath: /mnt/d/Documents/UIT/Nam_3/HK2/NT522_AI-ATTT/PPGT-GEN/static/js/evaluate_checker.js */
const form = document.getElementById('evaluate-form');
const submitBtn = document.getElementById('submit-btn');
const cancelBtn = document.getElementById('cancel-btn');
const btnText = document.getElementById('btn-text');
const testFileInput = document.getElementById('test-file');
const genPathInput = document.getElementById('gen-path');
const modeButtons = document.querySelectorAll('.mode-btn');
const modeInfos = document.querySelectorAll('.mode-info');

let currentMode = 'normal';
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
  
  // Update button text
  btnText.textContent = 'Bắt đầu đánh giá';
}

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
    
    resultElement.textContent = `❌ Quá trình đánh giá đã bị hủy bởi người dùng\n\nThời gian hủy: ${new Date().toLocaleString()}`;
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
  const modeIcon = currentMode === 'normal' ? '⚖️' : '🧠';
  const modeText = currentMode === 'normal' ? 'Normal' : 'DC';
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
    btnText.textContent = 'Đang đánh giá...';
  } else {
    submitBtn.classList.remove('loading');
    submitBtn.disabled = false;
    cancelBtn.classList.remove('show');
    btnText.textContent = 'Bắt đầu đánh giá';
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
    const formData = new FormData();
    formData.append('test_file', testFileInput.files[0]);
    formData.append('gen_path', genPathInput.value);
    formData.append('is_normal', currentMode === 'normal' ? 'true' : 'false');
    
    const requestOptions = {
      method: 'POST',
      signal: currentController.signal,
      body: formData
    };

    const res = await fetch('/evaluate_password_model', requestOptions);
    
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

// Thêm event listeners cho chart functionality
document.getElementById('chart-btn').addEventListener('click', toggleChart);
document.getElementById('chart-toggle-btn').addEventListener('click', hideChart);

function toggleChart() {
  const chartContainer = document.getElementById('chart-container');
  const chartBtn = document.getElementById('chart-btn');
  
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
  
  chartContainer.classList.add('hiding');
  setTimeout(() => {
    chartContainer.style.display = 'none';
    chartContainer.classList.remove('hiding');
    chartBtn.innerHTML = '📊 Biểu đồ';
  }, 300);
}

function displayResult(result, isSuccess) {
  window.lastEvaluateResult = result;
  
  const checkTime = checkStartTime ? 
    Math.round((Date.now() - checkStartTime) / 1000) : 0;
  document.getElementById('check-time').textContent = `${checkTime}s`;
  
  const resultElement = document.getElementById('result');
  const statusBadge = document.getElementById('status-badge');
  const chartBtn = document.getElementById('chart-btn');
  const chartImage = document.getElementById('chart-image');
  
  // THÊM: Xử lý biểu đồ
  if (result.chart) {
    chartBtn.style.display = 'inline-block';
    chartImage.src = `data:image/png;base64,${result.chart}`;
    
    // Auto show chart for first time
    setTimeout(() => {
      if (document.getElementById('chart-container').style.display === 'none') {
        toggleChart();
      }
    }, 500);
  } else {
    chartBtn.style.display = 'none';
    document.getElementById('chart-container').style.display = 'none';
  }
  
  let resultText = `⚖️ BÁO CÁO ĐÁNH GIÁ MODEL TẠO MẬT KHẨU\n`;
  resultText += `Thời gian: ${result.timestamp}\n`;
  resultText += `Mode: ${currentMode.toUpperCase()}\n`;
  resultText += `Test file: ${result.test_file}\n`;
  resultText += `Generated path: ${result.gen_path}\n`;
  resultText += `${'='.repeat(60)}\n\n`;
  
  resultText += `📊 KẾT QUẢ ĐÁNH GIÁ:\n`;
  
  // FIXED: Hiển thị giá trị chính xác với nhiều chữ số thập phân hơn
  const hitRateRaw = result.hit_rate;
  const repeatRateRaw = result.repeat_rate;
  
  // Hiển thị giá trị raw với 15 chữ số thập phân
  resultText += `Hit Rate: ${hitRateRaw.toFixed(15)}\n`;
  resultText += `Hit Rate (%): ${(hitRateRaw * 100).toFixed(12)}%\n`;
  resultText += `Repeat Rate: ${repeatRateRaw.toFixed(15)}\n`;
  resultText += `Repeat Rate (%): ${(repeatRateRaw * 100).toFixed(12)}%\n\n`;
  
  // THÊM: Scientific notation nếu số quá nhỏ
  if (repeatRateRaw < 0.001) {
    resultText += `📋 SCIENTIFIC NOTATION:\n`;
    resultText += `Hit Rate: ${hitRateRaw.toExponential(8)}\n`;
    resultText += `Repeat Rate: ${repeatRateRaw.toExponential(8)}\n\n`;
  }
  
  // THÊM: Thông báo về biểu đồ
  if (result.chart) {
    resultText += `📊 BIỂU ĐỒ PHÂN TÍCH:\n`;
    resultText += `✅ Biểu đồ chi tiết đã được tạo - nhấn nút "📊 Biểu đồ" để xem\n`;
    resultText += `   • Hit Rate vs Repeat Rate comparison\n`;
    resultText += `   • Password distribution analysis\n`;
    resultText += `   • Performance score breakdown\n`;
    resultText += `   • Model efficiency metrics\n\n`;
  }
  
  // Phân tích chi tiết
  resultText += `📈 PHÂN TÍCH CHI TIẾT:\n`;
  resultText += `Tổng số mật khẩu test: ${result.details.total_test_passwords.toLocaleString()}\n`;
  resultText += `Tổng số mật khẩu generated: ${result.details.total_generated_passwords.toLocaleString()}\n`;
  resultText += `Số mật khẩu trúng: ${result.details.hits.toLocaleString()}\n`;
  resultText += `Số mật khẩu unique trong generated: ${result.details.unique_generated.toLocaleString()}\n`;
  resultText += `Số mật khẩu lặp lại: ${result.details.repeats.toLocaleString()}\n`;
  resultText += `Số file đã xử lý: ${result.details.files_processed}\n\n`;
  
  // Thêm thông tin chi tiết hơn với độ chính xác cao
  resultText += `🔍 THÔNG TIN CHI TIẾT (ĐỘ CHÍNH XÁC CAO):\n`;
  const hitRatePercent = hitRateRaw * 100;
  const repeatRatePercent = repeatRateRaw * 100;
  const uniqueRatio = (result.details.unique_generated / result.details.total_generated_passwords) * 100;
  
  resultText += `Tỷ lệ unique trong generated: ${uniqueRatio.toFixed(10)}%\n`;
  resultText += `Tỷ lệ hit trên tổng generated: ${(result.details.hits / result.details.total_generated_passwords * 100).toFixed(10)}%\n`;
  resultText += `Tỷ lệ coverage test set: ${(result.details.hits / result.details.total_test_passwords * 100).toFixed(10)}%\n\n`;
  
  // Đánh giá hiệu suất với độ chính xác cao
  resultText += `🎯 ĐÁNH GIÁ HIỆU SUẤT (ĐỘ CHÍNH XÁO CAO):\n`;
  
  // Hit Rate evaluation với nhiều chữ số
  if (hitRatePercent >= 15) {
    resultText += `✅ Hit Rate: Xuất sắc (≥15.000000%) - Actual: ${hitRatePercent.toFixed(8)}%\n`;
  } else if (hitRatePercent >= 10) {
    resultText += `🟡 Hit Rate: Tốt (10.000000-15.000000%) - Actual: ${hitRatePercent.toFixed(8)}%\n`;
  } else if (hitRatePercent >= 5) {
    resultText += `🟠 Hit Rate: Trung bình (5.000000-10.000000%) - Actual: ${hitRatePercent.toFixed(8)}%\n`;
  } else if (hitRatePercent >= 1) {
    resultText += `🔴 Hit Rate: Yếu (1.000000-5.000000%) - Actual: ${hitRatePercent.toFixed(8)}%\n`;
  } else {
    resultText += `💀 Hit Rate: Rất yếu (<1.000000%) - Actual: ${hitRatePercent.toFixed(8)}%\n`;
  }
  
  // Repeat Rate evaluation với độ chính xác cực cao
  if (repeatRatePercent <= 0.000001) {
    resultText += `✅ Repeat Rate: Xuất sắc (≤0.000001%) - Actual: ${repeatRatePercent.toFixed(10)}%\n`;
  } else if (repeatRatePercent <= 0.001) {
    resultText += `🟢 Repeat Rate: Rất tốt (≤0.001000%) - Actual: ${repeatRatePercent.toFixed(10)}%\n`;
  } else if (repeatRatePercent <= 0.1) {
    resultText += `🟡 Repeat Rate: Tốt (≤0.100000%) - Actual: ${repeatRatePercent.toFixed(8)}%\n`;
  } else if (repeatRatePercent <= 1) {
    resultText += `🟠 Repeat Rate: Trung bình (≤1.000000%) - Actual: ${repeatRatePercent.toFixed(8)}%\n`;
  } else if (repeatRatePercent <= 5) {
    resultText += `🔴 Repeat Rate: Yếu (1.000000-5.000000%) - Actual: ${repeatRatePercent.toFixed(8)}%\n`;
  } else {
    resultText += `💀 Repeat Rate: Rất yếu (>5.000000%) - Actual: ${repeatRatePercent.toFixed(8)}%\n`;
  }
  
  // Overall score
  const overallScore = calculateOverallScore(result.hit_rate, result.repeat_rate);
  resultText += `\n🏆 ĐIỂM TỔNG THỂ: ${overallScore.score.toFixed(4)}/10.0000 (${overallScore.grade})\n`;
  
  // Thêm thông tin về efficiency với độ chính xác cao
  resultText += `\n📊 HIỆU SUẤT (ĐỘ CHÍNH XÁC CAO):\n`;
  const efficiencyScore = hitRateRaw / (repeatRateRaw + 0.000000001) * 100;
  const qualityIndex = (hitRatePercent * uniqueRatio) / 10000;
  
  resultText += `Efficiency Score: ${efficiencyScore.toFixed(6)}\n`;
  resultText += `Quality Index: ${qualityIndex.toFixed(10)}\n`;
  
  // THÊM: Raw data section
  resultText += `\n🔬 RAW DATA (EXACT VALUES):\n`;
  resultText += `Hit Rate (raw): ${hitRateRaw}\n`;
  resultText += `Repeat Rate (raw): ${repeatRateRaw}\n`;
  resultText += `Hit Rate (scientific): ${hitRateRaw.toExponential(12)}\n`;
  resultText += `Repeat Rate (scientific): ${repeatRateRaw.toExponential(12)}\n`;
  
  // Recommendations với thông tin chi tiết hơn
  resultText += `\n💡 KHUYẾN NGHỊ CHI TIẾT:\n`;
  if (hitRatePercent < 1) {
    resultText += `  🔥 CRITICAL: Hit Rate rất thấp (${hitRatePercent.toFixed(8)}%), cần training lại model\n`;
  } else if (hitRatePercent < 5) {
    resultText += `  ⚠️  WARNING: Hit Rate thấp (${hitRatePercent.toFixed(8)}%), cần fine-tune model\n`;
  } else if (hitRatePercent < 10) {
    resultText += `  ℹ️  INFO: Hit Rate có thể cải thiện (${hitRatePercent.toFixed(8)}%)\n`;
  } else {
    resultText += `  ✅ GOOD: Hit Rate đạt mức tốt (${hitRatePercent.toFixed(8)}%)\n`;
  }
  
  if (repeatRatePercent > 1) {
    resultText += `  🔥 CRITICAL: Repeat Rate cao (${repeatRatePercent.toFixed(8)}%), cần tăng diversity\n`;
  } else if (repeatRatePercent > 0.1) {
    resultText += `  ⚠️  WARNING: Repeat Rate hơi cao (${repeatRatePercent.toFixed(8)}%)\n`;
  } else if (repeatRatePercent < 0.000001) {
    resultText += `  ✅ EXCELLENT: Repeat Rate cực thấp (${repeatRatePercent.toFixed(10)}%), diversity xuất sắc\n`;
  } else {
    resultText += `  ✅ GOOD: Repeat Rate thấp (${repeatRatePercent.toFixed(8)}%), diversity tốt\n`;
  }
  
  if (hitRatePercent >= 5 && repeatRatePercent <= 0.1) {
    resultText += `  🎉 Model đang hoạt động rất tốt với hit rate cao và repeat rate thấp!\n`;
  }
  
  // Show sample matches if available
  if (result.sample_matches && result.sample_matches.length > 0) {
    resultText += `\n📝 MẪU MẬT KHẨU TRÚNG (${Math.min(15, result.sample_matches.length)} mẫu đầu tiên):\n`;
    result.sample_matches.slice(0, 15).forEach((password, index) => {
      resultText += `  ${(index + 1).toString().padStart(2, '0')}. ${password}\n`;
    });
    
    if (result.sample_matches.length > 15) {
      resultText += `  ... và ${result.sample_matches.length - 15} mật khẩu khác\n`;
    }
  }
  
  // Thêm timestamp và signature
  resultText += `\n${'='.repeat(60)}\n`;
  if (result.chart) {
    resultText += `📊 Biểu đồ phân tích chi tiết có sẵn - xem phía trên\n`;
  }
  resultText += `Generated by PagPassGPT Evaluator v1.0\n`;
  resultText += `Report generated at: ${new Date().toISOString()}\n`;
  resultText += `High-precision evaluation results preserved\n`;
  
  resultElement.textContent = resultText;
  
  // Set status badge based on overall performance với logic chi tiết hơn
  if (overallScore.score >= 9) {
    statusBadge.textContent = 'Hoàn hảo';
    statusBadge.className = 'status-badge status-excellent';
  } else if (overallScore.score >= 7) {
    statusBadge.textContent = 'Xuất sắc';
    statusBadge.className = 'status-badge status-excellent';
  } else if (overallScore.score >= 5) {
    statusBadge.textContent = 'Tốt';
    statusBadge.className = 'status-badge status-good';
  } else if (overallScore.score >= 3) {
    statusBadge.textContent = 'Trung bình';
    statusBadge.className = 'status-badge status-average';
  } else {
    statusBadge.textContent = 'Yếu';
    statusBadge.className = 'status-badge status-poor';
  }
  
  showResult();
}

function calculateOverallScore(hitRate, repeatRate) {
  // Hit rate component (0-6 points, higher is better) - scale mở rộng với độ chính xác cao
  let hitScore = 0;
  const hitPercent = hitRate * 100;
  if (hitPercent >= 20) hitScore = 6;
  else if (hitPercent >= 15) hitScore = 5.5;
  else if (hitPercent >= 10) hitScore = 5;
  else if (hitPercent >= 5) hitScore = 4;
  else if (hitPercent >= 2) hitScore = 3;
  else if (hitPercent >= 1) hitScore = 2;
  else if (hitPercent >= 0.5) hitScore = 1.5;
  else if (hitPercent >= 0.1) hitScore = 1;
  else hitScore = 0.5;
  
  // Repeat rate component (0-4 points, lower is better) - scale chi tiết hơn với độ chính xác cao
  let repeatScore = 0;
  const repeatPercent = repeatRate * 100;
  if (repeatPercent <= 0.000001) repeatScore = 4;        // Gần như hoàn hảo
  else if (repeatPercent <= 0.00001) repeatScore = 3.8;  // Xuất sắc
  else if (repeatPercent <= 0.0001) repeatScore = 3.6;   // Rất tốt
  else if (repeatPercent <= 0.001) repeatScore = 3.4;    // Tốt
  else if (repeatPercent <= 0.01) repeatScore = 3.2;     // Khá tốt
  else if (repeatPercent <= 0.1) repeatScore = 3;        // Ổn
  else if (repeatPercent <= 1) repeatScore = 2;          // Trung bình
  else if (repeatPercent <= 5) repeatScore = 1;          // Yếu
  else repeatScore = 0;                                   // Rất yếu
  
  const totalScore = hitScore + repeatScore;
  
  let grade = '';
  if (totalScore >= 9.5) grade = 'A+';
  else if (totalScore >= 9) grade = 'A';
  else if (totalScore >= 8.5) grade = 'A-';
  else if (totalScore >= 8) grade = 'B+';
  else if (totalScore >= 7) grade = 'B';
  else if (totalScore >= 6) grade = 'B-';
  else if (totalScore >= 5) grade = 'C+';
  else if (totalScore >= 4) grade = 'C';
  else if (totalScore >= 3) grade = 'C-';
  else if (totalScore >= 2) grade = 'D';
  else grade = 'F';
  
  return { score: totalScore, grade };
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
    a.download = `model-evaluation-${currentMode}-${Date.now()}.txt`;
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