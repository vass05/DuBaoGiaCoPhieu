/**
 * evaluate.js - Vẽ biểu đồ so sánh Thực tế vs Dự báo trên tập Test
 */

document.addEventListener('DOMContentLoaded', function () {
    if (typeof evalDataConfig !== 'undefined' && evalDataConfig.actual && evalDataConfig.actual.length > 0) {
        renderEvaluationChart(evalDataConfig.dates, evalDataConfig.actual, evalDataConfig.predicted);
    }
});

function renderEvaluationChart(dates, actualData, predictedData) {
    const ctx = document.getElementById('evalChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Giá thực tế (Actual Close Price)',
                    data: actualData,
                    borderColor: '#0f172a', // Đen than tối giản
                    borderWidth: 1.8,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    tension: 0.1,
                    fill: false
                },
                {
                    label: 'Giá dự báo mô hình RNN (Predicted Price)',
                    data: predictedData,
                    borderColor: '#b91c1c', // Đỏ đô thanh lịch
                    borderWidth: 1.6,
                    borderDash: [5, 4],
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    tension: 0.1,
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
                        font: { size: 12.5 },
                        color: '#334155'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return `${context.dataset.label}: $${context.parsed.y.toFixed(2)} USD`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: '#f8fafc'
                    },
                    ticks: {
                        color: '#64748b',
                        font: { size: 11 },
                        maxTicksLimit: 14
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
