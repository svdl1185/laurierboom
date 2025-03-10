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
      
      // Group data by time control
      // const bulletData = data.filter(item => item.time_control === 'bullet');
      const blitzData = data.filter(item => item.time_control === 'blitz');
      const rapidData = data.filter(item => item.time_control === 'rapid');
      // const classicalData = data.filter(item => item.time_control === 'classical');
      
      // Process data for each time control
      const processedData = {
        // bullet: processByDateWithFallback(bulletData),
        blitz: processByDateWithFallback(blitzData),
        rapid: processByDateWithFallback(rapidData),
        // classical: processByDateWithFallback(classicalData),
      };
      
      // Extract all dates for x-axis
      const allDates = [...new Set(data.map(item => item.date))].sort();
      
      // Find global min and max ratings for y-axis scale
      const allRatings = [
        // ...processedData.bullet.map(item => item.rating),
        ...processedData.blitz.map(item => item.rating),
        ...processedData.rapid.map(item => item.rating),
        // ...processedData.classical.map(item => item.rating),
      ].filter(rating => rating !== null);
      
      const minRating = Math.min(...allRatings, 1400) - 50;
      const maxRating = Math.max(...allRatings, 1600) + 50;
      
      // Create the chart
      const ctx = canvas.getContext('2d');
      const chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: allDates,
          datasets: [
            // Bullet dataset removed completely
            {
              label: 'Blitz',
              data: processedData.blitz,
              borderColor: 'rgba(54, 162, 235, 1)',
              backgroundColor: 'rgba(54, 162, 235, 0.2)',
              borderWidth: 2,
              pointBackgroundColor: 'rgba(54, 162, 235, 1)',
              pointBorderColor: '#fff',
              pointBorderWidth: 1,
              pointRadius: 4,
              pointHoverRadius: 6,
              tension: 0.1,
              parsing: {
                xAxisKey: 'date',
                yAxisKey: 'rating'
              }
            },
            {
              label: 'Rapid',
              data: processedData.rapid,
              borderColor: 'rgba(75, 192, 192, 1)',
              backgroundColor: 'rgba(75, 192, 192, 0.2)',
              borderWidth: 2,
              pointBackgroundColor: 'rgba(75, 192, 192, 1)',
              pointBorderColor: '#fff',
              pointBorderWidth: 1,
              pointRadius: 4,
              pointHoverRadius: 6,
              tension: 0.1,
              parsing: {
                xAxisKey: 'date',
                yAxisKey: 'rating'
              }
            }
            // Classical dataset removed completely
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'top',
            },
            tooltip: {
              callbacks: {
                afterLabel: function(context) {
                  const dataIndex = context.dataIndex;
                  const datasetIndex = context.datasetIndex;
                  const datasetLabel = context.dataset.label.toLowerCase();
                  const dataArray = processedData[datasetLabel];
                  
                  if (!dataArray[dataIndex] || !dataArray[dataIndex].tournament) {
                    return [];
                  }
                  
                  return [
                    `Tournament: ${dataArray[dataIndex].tournament}`,
                    dataArray[dataIndex].opponent ? `Opponent: ${dataArray[dataIndex].opponent}` : ''
                  ].filter(line => line);
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
    
  // Helper function to process data by date and fill in gaps
  function processByDateWithFallback(data) {
    if (!data || data.length === 0) return [];
    
    // Group data by date and take the last rating for each date
    const groupedData = {};
    data.forEach(item => {
      const date = item.date;
      groupedData[date] = item;
    });
    
    // Convert back to array
    return Object.values(groupedData);
  }
});