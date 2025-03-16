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
      
      // Define the bright green color used throughout the site
      const brightGreen = '#19e893';
      
      // Create datasets for each time control with unified color scheme
      const datasets = timeControls.map(timeControl => {
        const controlData = data.filter(item => item.time_control === timeControl);
        
        return {
          label: timeControl.charAt(0).toUpperCase() + timeControl.slice(1),
          data: controlData.map(item => ({
            x: item.date,
            y: item.rating,
            tournament: item.tournament,
            date: item.date,
            location: item.location || 'De Laurierboom, Amsterdam'
          })),
          borderColor: brightGreen,
          backgroundColor: brightGreen + '20', // Add transparency
          borderWidth: 3,
          pointBackgroundColor: brightGreen,
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
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
              display: false  // Hide the legend to make it cleaner
            },
            tooltip: {
              backgroundColor: 'rgba(26, 39, 33, 0.9)',
              titleColor: '#fff',
              bodyColor: '#fff',
              titleFont: {
                family: "'Roboto', sans-serif",
                weight: 'bold',
                size: 14
              },
              bodyFont: {
                family: "'Roboto', sans-serif",
                size: 13
              },
              padding: 10,
              cornerRadius: 6,
              displayColors: false,
              callbacks: {
                title: function(context) {
                  // Tournament name as title
                  return context[0].raw.tournament;
                },
                label: function(context) {
                  // Cleaner, more organized tooltip content
                  let ratingText = Math.round(context.raw.y);
                  let dateText = context.raw.date;
                  
                  // Return a simplified, cleaner label
                  return [
                    `Rating: ${ratingText}`,
                    `Date: ${dateText}`
                  ];
                }
              },
              // Clean tooltip layout
              titleMarginBottom: 8,
              bodySpacing: 4,
              xPadding: 10,
              yPadding: 10,
              caretPadding: 5,
              boxPadding: 3
            }
          },
          scales: {
            y: {
              min: minRating,
              max: maxRating,
              title: {
                display: true,
                text: 'Rating',
                font: {
                  weight: 'bold',
                  size: 14
                },
                color: '#333'
              },
              grid: {
                color: 'rgba(200, 200, 200, 0.1)'
              },
              ticks: {
                color: '#666',
                font: {
                  size: 12
                }
              }
            },
            x: {
              display: false  // Hide the x-axis completely
            }
          },
          elements: {
            line: {
              tension: 0.3  // Makes the line slightly smoother
            }
          },
          interaction: {
            intersect: false,
            mode: 'nearest'
          },
          layout: {
            padding: {
              top: 10,
              right: 20,
              bottom: 10,
              left: 10
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