/**
 * custom.js - Xử lý nhập số liệu thủ công và upload CSV
 */

let customChartInstance = null;

document.addEventListener('DOMContentLoaded', function () {
    const btnLoadSample = document.getElementById('btn-load-sample');
    const btnClearText = document.getElementById('btn-clear-text');
    const btnSubmitText = document.getElementById('btn-submit-text');
    const textInput = document.getElementById('custom-text-input');
    const daysSelect = document.getElementById('custom-days-select');

    const fileInput = document.getElementById('file-input');
    const fileChosenText = document.getElementById('file-chosen-text');
    const csvForm = document.getElementById('csv-upload-form');

    // 1. Tải 60 số mẫu
    if (btnLoadSample) {
        btnLoadSample.addEventListener('click', async function () {
            try {
                const res = await fetch('/api/sample-data');
                const data = await res.json();
                if (data.success) {
                    textInput.value = data.text;
                    showMessage('Đã điền thành công 60 giá đóng cửa mẫu từ cổ phiếu AAPL.', 'info');
                }
            } catch (e) {
                showMessage('Không thể tải dữ liệu mẫu.', 'error');
            }
        });
    }

    // 2. Xóa ô nhập
    if (btnClearText) {
        btnClearText.addEventListener('click', function () {
            textInput.value = '';
            hideResults();
        });
    }

    // 3. Gửi dữ liệu chuỗi số
    if (btnSubmitText) {
        btnSubmitText.addEventListener('click', async function () {
            const rawText = textInput.value.trim();
            if (!rawText) {
                showMessage('Vui lòng nhập danh sách giá hoặc nhấn nút "Điền 60 Giá Mẫu Thực Tế".', 'warning');
                return;
            }

            btnSubmitText.disabled = true;
            btnSubmitText.textContent = 'Đang tính toán...';

            try {
                const res = await fetch('/api/predict-custom', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: rawText,
                        days: parseInt(daysSelect.value)
                    })
                });

                const data = await res.json();
                if (data.success) {
                    showMessage(`Đã nạp ${data.count_provided} mức giá và dự báo thành công ${data.predictions.length} phiên tiếp theo!`, 'info');
                    displayResults(data, 'Dữ liệu nhập trực tiếp');
                } else {
                    showMessage('Lỗi: ' + (data.message || 'Không thể xử lý dữ liệu.'), 'error');
                }
            } catch (err) {
                showMessage('Lỗi kết nối khi gửi dữ liệu.', 'error');
            } finally {
                btnSubmitText.disabled = false;
                btnSubmitText.textContent = 'Chạy Dự Báo';
            }
        });
    }

    // 4. Chọn file CSV
    if (fileInput) {
        fileInput.addEventListener('change', function () {
            if (fileInput.files.length > 0) {
                fileChosenText.textContent = `Đã chọn: ${fileInput.files[0].name} (${(fileInput.files[0].size / 1024).toFixed(1)} KB)`;
            } else {
                fileChosenText.textContent = 'Chưa chọn tệp tin nào (Định dạng .csv)';
            }
        });
    }

    // 5. Gửi file CSV
    if (csvForm) {
        csvForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            if (!fileInput.files.length) {
                showMessage('Vui lòng chọn một tệp tin .csv.', 'warning');
                return;
            }

            const submitBtn = document.getElementById('btn-submit-csv');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Đang xử lý CSV...';

            const formData = new FormData(csvForm);

            try {
                const res = await fetch('/api/upload-csv', {
                    method: 'POST',
                    body: formData
                });

                const data = await res.json();
                if (data.success) {
                    showMessage(`Đã trích xuất thành công ${data.total_rows} dòng từ cột "${data.column_used}" trong tệp ${data.filename}.`, 'info');
                    displayResults(data, `Tệp: ${data.filename} (Cột: ${data.column_used})`);
                } else {
                    showMessage('Lỗi tải tệp: ' + (data.message || 'Dữ liệu không hợp lệ.'), 'error');
                }
            } catch (err) {
                showMessage('Có lỗi kết nối máy chủ.', 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Tải Lên & Dự Báo';
            }
        });
    }
});

function showMessage(msg, type = 'info') {
    const el = document.getElementById('custom-message');
    el.className = `alert alert-${type}`;
    el.textContent = msg;
    el.style.display = 'block';
}

function hideResults() {
    const resArea = document.getElementById('custom-results-area');
    if (resArea) resArea.style.display = 'none';
    const msg = document.getElementById('custom-message');
    if (msg) msg.style.display = 'none';
}

function displayResults(data, sourceLabel) {
    const resArea = document.getElementById('custom-results-area');
    resArea.style.display = 'block';

    // 1. Cập nhật thẻ
    document.getElementById('custom-card-latest').textContent = `$${data.latest_price.toFixed(2)}`;
    document.getElementById('custom-card-source').textContent = sourceLabel;
    document.getElementById('custom-card-next').textContent = `$${data.next_pred_price.toFixed(2)}`;

    const diffPrefix = data.diff > 0 ? '+' : '';
    const pctPrefix = data.pct > 0 ? '+' : '';
    document.getElementById('custom-card-diff').textContent = `${diffPrefix}${data.diff.toFixed(2)} USD`;
    document.getElementById('custom-card-pct').textContent = `${pctPrefix}${data.pct.toFixed(2)}%`;

    const badge = document.getElementById('custom-card-trend');
    badge.textContent = data.trend;
    badge.className = 'trend-badge ' + (data.trend === 'Tăng' ? 'up' : (data.trend === 'Giảm' ? 'down' : 'neutral'));

    // 2. Điền bảng
    const tbody = document.getElementById('custom-table-body');
    tbody.innerHTML = '';
    data.predictions.forEach(p => {
        const tr = document.createElement('tr');
        const diffP = p.change > 0 ? '+' : '';
        const pctP = p.change_percent > 0 ? '+' : '';
        const bClass = p.trend === 'Tăng' ? 'up' : (p.trend === 'Giảm' ? 'down' : 'neutral');

        tr.innerHTML = `
            <td><strong>T+${p.step}</strong></td>
            <td class="num">$${p.predicted_price.toFixed(2)}</td>
            <td class="num">${diffP}${p.change.toFixed(2)}</td>
            <td class="num">${pctP}${p.change_percent.toFixed(2)}%</td>
            <td><span class="trend-badge ${bClass}">${p.trend}</span></td>
        `;
        tbody.appendChild(tr);
    });

    // 3. Vẽ biểu đồ
    renderCustomChart(data.historical_subset, data.predictions);

    // Cuộn nhẹ tới kết quả
    resArea.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderCustomChart(historical, predictions) {
    const ctx = document.getElementById('customChart');
    if (!ctx) return;

    const labels = [];
    for (let i = 0; i < historical.length; i++) {
        labels.push(`-60 + ${i + 1}`);
    }

    const actualData = [...historical];
    const predictedData = new Array(historical.length - 1).fill(null);
    predictedData.push(historical[historical.length - 1]);

    predictions.forEach(p => {
        labels.push(`T+${p.step}`);
        actualData.push(null);
        predictedData.push(p.predicted_price);
    });

    if (customChartInstance) {
        customChartInstance.destroy();
    }

    customChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '60 mức giá đầu vào gần nhất',
                    data: actualData,
                    borderColor: '#334155',
                    borderWidth: 2,
                    pointRadius: 2,
                    tension: 0.15,
                    fill: false
                },
                {
                    label: 'Dự báo chuỗi tương lai',
                    data: predictedData,
                    borderColor: '#2563eb',
                    borderWidth: 2.2,
                    borderDash: [6, 4],
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#2563eb',
                    tension: 0.15,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            scales: {
                x: {
                    grid: { color: '#f8fafc' },
                    ticks: { color: '#64748b', font: { size: 11 }, maxTicksLimit: 12 }
                },
                y: {
                    grid: { color: '#f1f5f9' },
                    ticks: {
                        color: '#64748b',
                        font: { size: 11 },
                        callback: val => '$' + val
                    }
                }
            }
        }
    });
}
