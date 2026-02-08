document.addEventListener('DOMContentLoaded', function () {
    const toggleBtn = document.getElementById('toggleChartBtn');
    const chartContainer = document.getElementById('chartContainer');
    const percentageView = document.getElementById('percentageView');
    const ctx = document.getElementById('tasksChart');

    if (!toggleBtn || !ctx) return; // Not on dashboard or missing elements

    // Data from data attributes (populated in template)
    const data = JSON.parse(document.getElementById('chartData').textContent);

    let chartInstance = null;
    let isChartVisible = false;

    toggleBtn.addEventListener('click', () => {
        isChartVisible = !isChartVisible;

        if (isChartVisible) {
            // Show Chart
            percentageView.style.display = 'none';
            chartContainer.classList.add('active');
            toggleBtn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
        Show Percentage
      `;

            if (!chartInstance) {
                initChart(data);
            }
        } else {
            // Show Percentage
            chartContainer.classList.remove('active');
            setTimeout(() => {
                percentageView.style.display = 'block';
            }, 200); // Wait for fade out

            toggleBtn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path><path d="M22 12A10 10 0 0 0 12 2v10z"></path></svg>
        View Chart
      `;
        }
    });

    function initChart(stats) {
        chartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Completed', 'Pending', 'In Progress', 'Overdue'],
                datasets: [{
                    data: [stats.completed, stats.pending, stats.in_progress, stats.overdue],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.8)', // Success/Completed
                        'rgba(161, 161, 161, 0.5)', // Pending/Grey
                        'rgba(139, 92, 246, 0.8)', // In Progress/Purple
                        'rgba(239, 68, 68, 0.8)',  // Overdue/Red
                    ],
                    borderColor: [
                        'rgba(16, 185, 129, 1)',
                        'rgba(161, 161, 161, 1)',
                        'rgba(139, 92, 246, 1)',
                        'rgba(239, 68, 68, 1)',
                    ],
                    borderWidth: 1,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#a3a3a3',
                            font: {
                                family: 'Inter',
                                size: 12
                            },
                            padding: 20
                        }
                    }
                },
                cutout: '70%',
            }
        });
    }
});
