// static/chess/js/components/rating-chart.js
document.addEventListener('DOMContentLoaded', function() {
    const chartContainer = document.getElementById('rating-history-chart');
    if (!chartContainer) return;
    
    // Clear existing content to prevent duplicates
    chartContainer.innerHTML = '';
    
    // Create a canvas element for Chart.js
    const canvas = document.createElement('canvas');
    chartContainer.appendChild(canvas);
    
    // Get player ID from data attribute
    const playerId = chartContainer.getAttribute('data-player-id');
    
    // Fetch rating history data from your backend
    fetch(`/player/${playerId}/rating-history/`)
      .then(response => response.json())
      .then(data => {
        if (!data || data.length === 0) {
          chartContainer.innerHTML = '<div class="text-center py-4">No rating history available</div>';
          return;
        }
        
        // Group data by date and take the last rating for each date
        const groupedData = {};
        data.forEach(item => {
          // Use date as the key
          const date = item.date;
          
          // If this date already exists in our grouped data,
          // update it only if this is a newer entry (assuming data is chronological)
          groupedData[date] = item;
        });
        
        // Convert back to array
        const aggregatedData = Object.values(groupedData);
        
        // Sort by date (just to be safe)
        aggregatedData.sort((a, b) => new Date(a.date) - new Date(b.date));
        
        // Extract the dates and ratings from the aggregated data
        const dates = aggregatedData.map(item => item.date);
        const ratings = aggregatedData.map(item => item.rating);
        const tournaments = aggregatedData.map(item => item.tournament);
        const opponents = aggregatedData.map(item => item.opponent);
        
        // Find minimum and maximum ratings to set y-axis scale
        const minRating = Math.min(...ratings) - 20;
        const maxRating = Math.max(1500, ...ratings) + 20;
        
        // Create the chart
        const ctx = canvas.getContext('2d');
        const chart = new Chart(ctx, {
          type: 'line',
          data: {
            labels: dates,
            datasets: [{
              label: 'Rating',
              data: ratings,
              backgroundColor: 'rgba(58, 92, 170, 0.2)',
              borderColor: 'rgba(58, 92, 170, 1)',
              borderWidth: 2,
              pointBackgroundColor: 'rgba(58, 92, 170, 1)',
              pointBorderColor: '#fff',
              pointBorderWidth: 1,
              pointRadius: 5,
              pointHoverRadius: 7,
              tension: 0.1
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: false
              },
              tooltip: {
                callbacks: {
                  afterLabel: function(context) {
                    const index = context.dataIndex;
                    return [
                      `Tournament: ${tournaments[index]}`
                    ];
                  }
                }
              }
            },
            scales: {
              y: {
                min: minRating,
                max: maxRating,
                title: {
                  display: true,
                  text: 'Rating'
                }
              },
              x: {
                title: {
                  display: true,
                  text: 'Date'
                },
                ticks: {
                  maxRotation: 45,
                  minRotation: 45
                }
              }
            }
          }
        });
        
        // Set a fixed height for the container
        chartContainer.style.height = '300px';
      })
      .catch(error => {
        console.error('Error fetching rating history:', error);
        chartContainer.innerHTML = '<div class="text-center py-4">Error loading rating history</div>';
      });
  });