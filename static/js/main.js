/**
 * main.js - Xử lý biểu đồ và tương tác trên trang Dashboard
 * Hỗ trợ định dạng tiền tệ linh hoạt (VND cho cổ phiếu Việt Nam, USD cho cổ phiếu Mỹ)
 */

let stockChartInstance = null;

/**
 * Định dạng giá tiền theo thị trường (VND hoặc USD)
 */
function formatPrice(val, isVn = false) {
    if (val === null || val === undefined || isNaN(val)) return '-';
    if (isVn) {
        return Math.round(val).toLocaleString('vi-VN') + ' VND';
    }
    return '$' + Number(val).toFixed(2);
}

/**
 * Định dạng độ chênh lệch giá (có dấu +/-)
 */
function formatDiff(diff, isVn = false) {
    if (diff === null || diff === undefined || isNaN(diff)) return '-';
    const prefix = diff > 0 ? '+' : '';
    if (isVn) {
        return prefix + Math.round(diff).toLocaleString('vi-VN') + ' VND';
    }
    return prefix + Number(diff).toFixed(2) + ' USD';
}

document.addEventListener('DOMContentLoaded', function () {
    if (typeof initialConfig !== 'undefined' && initialConfig.dates && initialConfig.dates.length > 0) {
        renderMainChart(
            initialConfig.dates,
            initialConfig.closes,
            initialConfig.predictions,
            initialConfig.symbol,
            Boolean(initialConfig.is_vn)
        );
    }

    const stockSelect = document.getElementById('stock-select');
    const sourceSelect = document.getElementById('source-select');
    const daysSelect = document.getElementById('days-select');
    const form = document.getElementById('forecast-form');

    // Chỉ thực hiện dự báo khi người dùng nhấn nút "Thực Hiện Dự Báo" (submit form)
    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const symbol = stockSelect ? stockSelect.value : 'AAPL';
            const days = daysSelect ? daysSelect.value : 7;
            const source = sourceSelect ? sourceSelect.value : 'realtime';
            fetchForecastData(symbol, days, source);
        });
    }
});

/**
 * Gọi API lấy dữ liệu và cập nhật giao diện bất đồng bộ
 */
async function fetchForecastData(symbol, days, source = 'realtime') {
    const spinner = document.getElementById('loading-spinner');
    const btnSubmit = document.getElementById('btn-submit');
    if (spinner) spinner.style.display = 'inline-block';
    if (btnSubmit) btnSubmit.disabled = true;

    try {
        const response = await fetch(`/api/stock/${encodeURIComponent(symbol)}?days=${days}&source=${encodeURIComponent(source)}`);
        const data = await response.json();

        if (!data.success) {
            alert('Thông báo: ' + (data.message || 'Không thể lấy dữ liệu cho mã này.'));
            return;
        }

        const isVn = Boolean(data.is_vn || (data.symbol && data.symbol.endsWith('.VN')));
        const forecastDays = parseInt(data.forecast_days || days || 1, 10);

        // 1. Cập nhật các thẻ chỉ số
        const latestPriceEl = document.getElementById('card-latest-price');
        if (latestPriceEl) latestPriceEl.textContent = formatPrice(data.latest_price, isVn);

        const latestDateEl = document.getElementById('card-latest-date');
        if (latestDateEl) latestDateEl.textContent = `Phiên ngày: ${data.latest_date || data.dates[data.dates.length - 1]}`;

        // Thẻ 2: Giá dự báo (cuối kỳ vs ngày tiếp theo)
        const cardPredTitle = document.getElementById('card-pred-title');
        const cardPredPrice = document.getElementById('card-pred-price');
        const cardPredSub = document.getElementById('card-pred-sub');

        if (forecastDays > 1) {
            if (cardPredTitle) cardPredTitle.textContent = `Giá dự báo cuối kỳ (T+${forecastDays})`;
            if (cardPredPrice) cardPredPrice.textContent = formatPrice(data.target_price || data.final_price || data.next_pred_price, isVn);
            if (cardPredSub) {
                cardPredSub.textContent = `Phiên T+1: ${formatPrice(data.day1_price, isVn)}`;
                cardPredSub.style.display = 'block';
            }
        } else {
            if (cardPredTitle) cardPredTitle.textContent = 'Giá dự báo ngày tiếp theo (T+1)';
            if (cardPredPrice) cardPredPrice.textContent = formatPrice(data.day1_price || data.next_pred_price, isVn);
            if (cardPredSub) cardPredSub.style.display = 'none';
        }

        // Thẻ 3: Biến động kỳ vọng (cả kỳ vs T+1)
        const cardDiffTitle = document.getElementById('card-diff-title');
        const cardDiff = document.getElementById('card-diff');
        const cardPct = document.getElementById('card-pct');
        const pctPrefix = data.pct > 0 ? '+' : '';

        if (forecastDays > 1) {
            if (cardDiffTitle) cardDiffTitle.textContent = `Biến động cả kỳ (${forecastDays} ngày)`;
            if (cardDiff) cardDiff.textContent = formatDiff(data.diff, isVn);
            let subText = `${pctPrefix}${data.pct.toFixed(2)}%`;
            if (data.day1_pct !== undefined && data.day1_pct !== null) {
                const day1Prefix = data.day1_pct > 0 ? '+' : '';
                subText += ` (T+1: ${day1Prefix}${data.day1_pct.toFixed(2)}%)`;
            }
            if (cardPct) cardPct.textContent = subText;
        } else {
            if (cardDiffTitle) cardDiffTitle.textContent = 'Biến động kỳ vọng (T+1)';
            if (cardDiff) cardDiff.textContent = formatDiff(data.diff, isVn);
            if (cardPct) cardPct.textContent = `${pctPrefix}${data.pct.toFixed(2)}%`;
        }

        // Thẻ 4: Xu hướng dự kiến
        const cardTrendTitle = document.getElementById('card-trend-title');
        const cardTrendBadge = document.getElementById('card-trend-badge');
        const cardTrendSub = document.getElementById('card-trend-sub');

        if (forecastDays > 1) {
            if (cardTrendTitle) cardTrendTitle.textContent = `Xu hướng kỳ ${forecastDays} ngày`;
            if (cardTrendSub) {
                cardTrendSub.textContent = `Phiên T+1: ${data.day1_trend || 'Đi ngang'}`;
                cardTrendSub.style.display = 'block';
            }
        } else {
            if (cardTrendTitle) cardTrendTitle.textContent = 'Xu hướng dự kiến';
            if (cardTrendSub) cardTrendSub.style.display = 'none';
        }

        if (cardTrendBadge) {
            cardTrendBadge.textContent = data.trend;
            cardTrendBadge.className = 'trend-badge ' + (data.trend === 'Tăng' ? 'up' : (data.trend === 'Giảm' ? 'down' : 'neutral'));
        }

        // 2. Cập nhật nhãn nguồn dữ liệu & tiêu đề biểu đồ
        const badgeContainer = document.getElementById('source-badge-container');
        if (badgeContainer) {
            if (data.source === 'realtime') {
                badgeContainer.innerHTML = '<span class="badge-source live" id="source-badge">⚡ Trực tuyến (Yahoo Finance)</span>';
            } else {
                badgeContainer.innerHTML = '<span class="badge-source offline" id="source-badge">📂 Ngoại tuyến (CSV 2018)</span>';
            }
        }

        document.getElementById('chart-panel-title').textContent =
            `Diễn Biến Giá & Dự Báo (${data.symbol})`;

        // Cập nhật giá trị đang chọn trong dropdown
        const sel = document.getElementById('stock-select');
        if (sel) {
            sel.value = data.symbol;
        }

        // 3. Cập nhật bảng dự báo & bảng lịch sử
        updateForecastTable(data.predictions, isVn);
        updateHistoryTable(data.dates, data.close_prices, data.open_prices, data.high_prices, data.low_prices, isVn);

        // 4. Vẽ lại biểu đồ
        renderMainChart(data.dates, data.close_prices, data.predictions, data.symbol, isVn);

    } catch (err) {
        console.error('Fetch error:', err);
        alert('Có lỗi xảy ra khi kết nối máy chủ. Vui lòng kiểm tra lại kết nối mạng.');
    } finally {
        if (spinner) spinner.style.display = 'none';
        if (btnSubmit) btnSubmit.disabled = false;
    }
}

/**
 * Cập nhật bảng 10 phiên giao dịch gần nhất
 */
function updateHistoryTable(dates, closes, opens, highs, lows, isVn = false) {
    const tbody = document.getElementById('history-table-body');
    if (!tbody || !dates) return;
    tbody.innerHTML = '';
    const len = dates.length;
    const start = Math.max(0, len - 10);
    for (let i = len - 1; i >= start; i--) {
        const tr = document.createElement('tr');
        const openVal = (opens && opens[i] !== undefined && opens[i] !== null) ? formatPrice(opens[i], isVn) : '-';
        const highVal = (highs && highs[i] !== undefined && highs[i] !== null) ? formatPrice(highs[i], isVn) : '-';
        const lowVal = (lows && lows[i] !== undefined && lows[i] !== null) ? formatPrice(lows[i], isVn) : '-';
        tr.innerHTML = `
            <td>${dates[i]}</td>
            <td class="num"><strong>${formatPrice(closes[i], isVn)}</strong></td>
            <td class="num">${openVal}</td>
            <td class="num">${highVal}</td>
            <td class="num">${lowVal}</td>
        `;
        tbody.appendChild(tr);
    }
}

/**
 * Cập nhật bảng các phiên dự báo
 */
function updateForecastTable(predictions, isVn = false) {
    const tbody = document.querySelector('#forecast-table tbody');
    if (!tbody) return;

    tbody.innerHTML = '';
    predictions.forEach(p => {
        const tr = document.createElement('tr');
        const pctPrefix = p.change_percent > 0 ? '+' : '';
        const badgeClass = p.trend === 'Tăng' ? 'up' : (p.trend === 'Giảm' ? 'down' : 'neutral');

        tr.innerHTML = `
            <td><strong>T+${p.step}</strong></td>
            <td class="num">${formatPrice(p.predicted_price, isVn)}</td>
            <td class="num">${formatDiff(p.change, isVn)}</td>
            <td class="num">${pctPrefix}${p.change_percent.toFixed(2)}%</td>
            <td><span class="trend-badge ${badgeClass}">${p.trend}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

/**
 * Khởi tạo hoặc cập nhật biểu đồ giá
 */
function renderMainChart(dates, historicalPrices, predictions, symbol, isVn = false) {
    const ctx = document.getElementById('stockChart');
    if (!ctx) return;

    // Chuẩn bị nhãn thời gian và dữ liệu nối tiếp
    const labels = [...dates];
    const actualData = [...historicalPrices];
    const predictedData = new Array(historicalPrices.length - 1).fill(null);

    // Điểm giao nhau giữa lịch sử và dự báo
    predictedData.push(historicalPrices[historicalPrices.length - 1]);

    predictions.forEach((p) => {
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
                                return `${context.dataset.label}: ${formatPrice(context.parsed.y, isVn)}`;
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
                            if (isVn) {
                                return Math.round(val).toLocaleString('vi-VN') + ' đ';
                            }
                            return '$' + val;
                        }
                    }
                }
            }
        }
    });
}
