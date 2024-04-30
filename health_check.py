import time

def update_health_status():
  """Updates the last health check time variable."""
  global last_health_check_time  # Declare the variable as global
  last_health_check_time = time.time()

# Optional: You can add additional health check logic here
# For example, checking database connection or external service status

# Make the variable accessible from outside the module (if needed)
last_health_check_time = None  # Initialize the variable
