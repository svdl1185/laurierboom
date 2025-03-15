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
      
      // Group data by tournament rather than by individual match
      const tournaments = {};
      
      // Group matches by tournament and date
      data.forEach(item => {
        const key = `${item.tournament}_${item.date}`;
        if (!tournaments[key]) {
          tournaments[key] = {
            date: item.date,
            tournament: item.tournament,
            rating: item.rating,
            time_control: item.time_control
          };
        }
      });
      
      // Convert to array and sort by date
      const processedData = Object.values(tournaments).sort((a, b) => 
        new Date(a.date) - new Date(b.date)
      );
      
      // Extract all dates for x-axis
      const allDates = [...new Set(processedData.map(item => item.date))].sort();
      
      // Find min and max ratings for y-axis scale
      const allRatings = processedData.map(item => item.rating).filter(rating => rating !== null);
      
      const minRating = Math.min(...allRatings, 1400) - 50;
      const maxRating = Math.max(...allRatings, 1600) + 50;
      
      // Create the chart
      const ctx = canvas.getContext('2d');
      const chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: allDates,
          datasets: [
            {
              label: 'Blitz',
              data: processedData.map(item => ({
                x: item.date,
                y: item.rating,
                tournament: item.tournament
              })),
              borderColor: 'rgba(54, 162, 235, 1)',
              backgroundColor: 'rgba(54, 162, 235, 0.2)',
              borderWidth: 2,
              pointBackgroundColor: 'rgba(54, 162, 235, 1)',
              pointBorderColor: '#fff',
              pointBorderWidth: 1,
              pointRadius: 4,
              pointHoverRadius: 6,
              tension: 0.1
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'top',
              labels: {
                boxWidth: 12
              }
            },
            tooltip: {
              callbacks: {
                title: function(context) {
                  return context[0].raw.tournament;
                },
                label: function(context) {
                  return 'Rating: ' + context.raw.y;
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