const socket = io();
let angleChart;
let anomalyTimeout;

document.addEventListener('DOMContentLoaded', () => {
    const ctx = document.getElementById('angleChart').getContext('2d');
    angleChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: 'Neck', data: [], borderColor: '#ef4444', backgroundColor: 'rgba(239,68,68,0.1)', fill: true, tension: 0.3 },
                { label: 'Trunk', data: [], borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.1)', fill: true, tension: 0.3 },
                { label: 'Upper Arm (L)', data: [], borderColor: '#10b981', backgroundColor: 'rgba(16,185,129,0.1)', fill: true, tension: 0.3 }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: { y: { beginAtZero: true, title: { display: true, text: 'Angle (degrees)' } } },
            plugins: { legend: { display: false } }
        }
    });
});

socket.on('pose_update', (data) => {
    // Update score cards
    document.getElementById('rula').innerText = data.rula;
    document.getElementById('reba').innerText = data.reba;
    const riskText = data.risk_level;
    document.getElementById('riskLevel').innerHTML = riskText;
    
    // Progress bars (RULA max 7, REBA max 15)
    const rulaPercent = (data.rula / 7) * 100;
    const rebaPercent = (data.reba / 15) * 100;
    document.getElementById('rulaProgress').style.width = `${Math.min(rulaPercent,100)}%`;
    document.getElementById('rebaProgress').style.width = `${Math.min(rebaPercent,100)}%`;
    
    // Risk tags color
    const rulaTag = document.getElementById('rulaRisk');
    rulaTag.innerText = riskText;
    rulaTag.style.background = getRiskColor(riskText);
    
    const rebaTag = document.getElementById('rebaRisk');
    rebaTag.innerText = riskText;
    rebaTag.style.background = getRiskColor(riskText);
    
    // Anomalies list
    const anomaliesDiv = document.getElementById('anomalies');
    if (data.anomalies && data.anomalies.length) {
        anomaliesDiv.innerHTML = data.anomalies.map(a => `<div>⚠️ ${a}</div>`).join('');
        if (anomalyTimeout) clearTimeout(anomalyTimeout);
        anomalyTimeout = setTimeout(() => { anomaliesDiv.innerHTML = ''; }, 5000);
    } else {
        anomaliesDiv.innerHTML = '<div style="color:var(--success)">✅ No anomalies</div>';
    }
    
    // Update chart
    const labels = angleChart.data.labels;
    const neckData = angleChart.data.datasets[0].data;
    const trunkData = angleChart.data.datasets[1].data;
    const armData = angleChart.data.datasets[2].data;
    const now = new Date().toLocaleTimeString();
    labels.push(now);
    neckData.push(data.angles.neck);
    trunkData.push(data.angles.trunk);
    armData.push(data.angles.upper_arm_left);
    if (labels.length > 30) {
        labels.shift();
        neckData.shift();
        trunkData.shift();
        armData.shift();
    }
    angleChart.update();
});

socket.on('config', (cfg) => {
    document.getElementById('mode').innerText = cfg.mode === 1 ? 'Single-view (2D)' : cfg.mode === 2 ? 'Dual-view' : 'Multi-view 3D';
    document.getElementById('camStatus').innerText = cfg.mode > 0 ? 'Active' : 'Disconnected';
    document.getElementById('imuStatus').innerText = 'Active (BMI270)';
});

function getRiskColor(level) {
    if (level.includes('Élevé') || level.includes('High')) return '#ef4444';
    if (level.includes('Moyen') || level.includes('Medium')) return '#f59e0b';
    return '#10b981';
}

// Theme toggle
const themeToggle = document.getElementById('themeToggle');
themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark');
    themeToggle.innerText = document.body.classList.contains('dark') ? '☀️' : '🌙';
});
if (localStorage.getItem('theme') === 'dark') document.body.classList.add('dark');