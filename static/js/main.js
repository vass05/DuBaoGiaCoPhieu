/**
 * main.js - Xử lý biểu đồ và tương tác trên trang Dashboard
 */

let stockChartInstance = null;

document.addEventListener('DOMContentLoaded', function () {
    if (typeof initialConfig !== 'undefined' && initialConfig.dates && initialConfig.dates.length > 0) {
        renderMainChart(initialConfig.dates, initialConfig.closes, initialConfig.predictions, initialConfig.symbol);
    }

    // Xử lý chuyển đổi nhanh mã cổ phiếu hoặc số ngày mà không cần reload trang
    const stockSelect = document.getElementById('stock-select');
    const daysSelect = document.getElementById('days-select');
    const form = document.getElementById('forecast-form');
    const spinner = document.getElementById('loading-spinner');

    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            fetchForecastData(stockSelect.value, daysSelect.value);
        });
    }
});

/**
 * Gọi API lấy dữ liệu và cập nhật giao diện bất đồng bộ
 */
async function fetchForecastData(symbol, days) {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) spinner.style.display = 'inline-block';

    try {
        const response = await fetch(`/api/stock/${encodeURIComponent(symbol)}?days=${days}`);
        const data = await response.json();

        if (!data.success) {
            alert('Lỗi: ' + (data.message || 'Không thể lấy dữ liệu.'));
            return;
        }

        // 1. Cập nhật các thẻ chỉ số
        document.getElementById('card-latest-price').textContent = `$${data.latest_price.toFixed(2)}`;
        document.getElementById('card-latest-date').textContent = `Phiên ngày: ${data.dates[data.dates.length - 1]}`;
        document.getElementById('card-pred-price').textContent = `$${data.next_pred_price.toFixed(2)}`;

        const diffPrefix = data.diff > 0 ? '+' : '';
        const pctPrefix = data.pct > 0 ? '+' : '';
        document.getElementById('card-diff').textContent = `${diffPrefix}${data.diff.toFixed(2)} USD`;
        document.getElementById('card-pct').textContent = `${pctPrefix}${data.pct.toFixed(2)}%`;

        const badge = document.getElementById('card-trend-badge');
        badge.textContent = data.trend;
        badge.className = 'trend-badge ' + (data.trend === 'Tăng' ? 'up' : (data.trend === 'Giảm' ? 'down' : 'neutral'));

        // 2. Cập nhật tiêu đề bảng
        document.getElementById('chart-panel-title').textContent =
            `Diễn Biến Giá & Dự Báo (${data.symbol})`;

        // 3. Cập nhật bảng dự báo
        updateForecastTable(data.predictions);

        // 4. Vẽ lại biểu đồ
        renderMainChart(data.dates, data.close_prices, data.predictions, data.symbol);

    } catch (err) {
        console.error('Fetch error:', err);
        alert('Có lỗi xảy ra khi kết nối máy chủ.');
    } finally {
        if (spinner) spinner.style.display = 'none';
    }
}

/**
 * Cập nhật bảng các phiên dự báo
 */
function updateForecastTable(predictions) {
    const tbody = document.querySelector('#forecast-table tbody');
    if (!tbody) return;

    tbody.innerHTML = '';
    predictions.forEach(p => {
        const tr = document.createElement('tr');
        const diffPrefix = p.change > 0 ? '+' : '';
        const pctPrefix = p.change_percent > 0 ? '+' : '';
        const badgeClass = p.trend === 'Tăng' ? 'up' : (p.trend === 'Giảm' ? 'down' : 'neutral');

        tr.innerHTML = `
            <td><strong>T+${p.step}</strong></td>
            <td class="num">$${p.predicted_price.toFixed(2)}</td>
            <td class="num">${diffPrefix}${p.change.toFixed(2)}</td>
            <td class="num">${pctPrefix}${p.change_percent.toFixed(2)}%</td>
            <td><span class="trend-badge ${badgeClass}">${p.trend}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

/**
 * Khởi tạo hoặc cập nhật biểu đồ giá
 */
function renderMainChart(dates, historicalPrices, predictions, symbol) {
    const ctx = document.getElementById('stockChart');
    if (!ctx) return;

    // Chuẩn bị nhãn thời gian và dữ liệu nối tiếp
    const labels = [...dates];
    const actualData = [...historicalPrices];
    const predictedData = new Array(historicalPrices.length - 1).fill(null);

    // Điểm giao nhau giữa lịch sử và dự báo
    predictedData.push(historicalPrices[historicalPrices.length - 1]);

    predictions.forEach((p, idx) => {
        labels.push(`T+${p.step}`);
        actualData.push(null);
        predictedData.push(p.predicted_price);
    });

    if (stockChartInstance) {
        stockChartInstance.destroy();
    }

    stockChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: `Giá đóng cửa thực tế (${symbol})`,
                    data: actualData,
                    borderColor: '#334155', // Màu slate trung tính
                    backgroundColor: 'rgba(241, 245, 249, 0.5)',
                    borderWidth: 2,
                    pointRadius: 2,
                    pointHoverRadius: 5,
                    tension: 0.15,
                    fill: false
                },
                {
                    label: 'Đường dự báo RNN',
                    data: predictedData,
                    borderColor: '#2563eb', // Xanh dương trang nhã
                    borderWidth: 2.2,
                    borderDash: [6, 4], // Nét đứt biểu thị dự báo
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
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        boxWidth: 14,
                        font: { size: 12.5, family: '-apple-system, sans-serif' },
                        color: '#334155'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            if (context.parsed.y !== null) {
                                return `${context.dataset.label}: $${context.parsed.y.toFixed(2)} USD`;
                            }
                            return null;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: '#f1f5f9'
                    },
                    ticks: {
                        color: '#64748b',
                        font: { size: 11 },
                        maxTicksLimit: 12
                    }
                },
                y: {
                    grid: {
                        color: '#f1f5f9'
                    },
                    ticks: {
                        color: '#64748b',
                        font: { size: 11 },
                        callback: function (val) {
                            return '$' + val;
                        }
                    }
                }
            }
        }
    });
}
