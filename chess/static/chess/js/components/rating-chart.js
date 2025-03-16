// Updated rating-chart.js with better data handling
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
      
      // Sort data by date if needed
      data.sort((a, b) => {
        return new Date(a.date) - new Date(b.date);
      });
      
      // Extract all dates for x-axis
      const allDates = data.map(item => item.date);
      
      // Find min and max ratings for y-axis scale with a bit of padding
      const allRatings = data.map(item => item.rating).filter(rating => rating !== null);
      
      const minRating = Math.floor((Math.min(...allRatings) - 50) / 100) * 100;
      const maxRating = Math.ceil((Math.max(...allRatings) + 50) / 100) * 100;
      
      // Group data by time control
      const timeControls = [...new Set(data.map(item => item.time_control))];
      
      // Create datasets for each time control
      const datasets = timeControls.map(timeControl => {
        const controlData = data.filter(item => item.time_control === timeControl);
        
        // Define colors based on time control
        let color;
        switch(timeControl) {
          case 'bullet':
            color = '#ff4d4d';
            break;
          case 'blitz':
            color = '#4da6ff';
            break;
          case 'rapid':
            color = '#4dff4d';
            break;
          case 'classical':
            color = '#9966ff';
            break;
          default:
            color = '#19e893';  // Default green color from your theme
        }
        
        return {
          label: timeControl.charAt(0).toUpperCase() + timeControl.slice(1),
          data: controlData.map(item => ({
            x: item.date,
            y: item.rating,
            tournament: item.tournament
          })),
          borderColor: color,
          backgroundColor: color + '20', // Add transparency
          borderWidth: 2,
          pointBackgroundColor: color,
          pointBorderColor: '#fff',
          pointBorderWidth: 1,
          pointRadius: 5,
          pointHoverRadius: 8,
          tension: 0.2,
          fill: false
        };
      });
      
      // Create the chart
      const ctx = canvas.getContext('2d');
      const chart = new Chart(ctx, {
        type: 'line',
        data: { datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'top',
              labels: {
                boxWidth: 12,
                color: '#666'
              }
            },
            tooltip: {
              backgroundColor: '#1a2721',
              titleColor: '#fff',
              bodyColor: '#fff',
              titleFont: {
                family: "'Roboto', sans-serif",
                weight: 'bold',
                size: 14
              },
              bodyFont: {
                family: "'Roboto', sans-serif",
                size: 14
              },
              padding: 12,
              cornerRadius: 8,
              displayColors: false,
              callbacks: {
                title: function(context) {
                  return context[0].raw.tournament;
                },
                label: function(context) {
                  return 'Rating: ' + Math.round(context.raw.y); // Ensure integer display
                }
              },
              // Custom tooltip layout
              titleMarginBottom: 8,
              bodySpacing: 6,
              xPadding: 12,
              yPadding: 12
            }
          },
          scales: {
            y: {
              min: minRating,
              max: maxRating,
              title: {
                display: true,
                text: 'Rating'
              },
              grid: {
                color: 'rgba(200, 200, 200, 0.1)'
              },
              ticks: {
                color: '#666'
              }
            },
            x: {
              title: {
                display: true,
                text: 'Date'
              },
              ticks: {
                color: '#666',
                maxRotation: 45,
                minRotation: 45
              },
              grid: {
                display: false
              }
            }
          },
          elements: {
            line: {
              tension: 0.4 // Makes the line smoother
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