# Invidious_Cast
Invidious Cast is a Flask application that generates RSS feeds for podcasts based on YouTube channels. It allows you to customize the podcast feed format and includes support for iTunes-specific tags.

Table of Contents
Features
Installation
Using Docker
Usage
Configuration
Contributing
License
Features
Convert YouTube channel content into podcast RSS feeds.
Support for audio and video formats with customizable URLs.
Automatic handling of iTunes-specific tags for improved compatibility.
Installation
Using Docker
Clone the repository:

bash
Copy code
git clone https://github.com/yourusername/invidious-cast.git
Build the Docker image:

bash
Copy code
cd invidious-cast
docker build -t invidious-cast .
Run the Docker container:

bash
Copy code
docker run -d -p 5895:5895 --name invidious-cast-app invidious-cast
Usage
Access the application at http://localhost:5895 in your web browser.

Configuration
PERMITTED_SOURCES: Comma-separated list of permitted sources for podcast content.
PORT: Port number for the Flask application (default is 5895).
DEBUG: Enable Flask debug mode (True or False, default is False).
Contributing
Fork the repository.
Create a new branch (git checkout -b feature-branch).
Make your changes.
Commit your changes (git commit -am 'Add new feature').
Push to the branch (git push origin feature-branch).
Create a new Pull Request.
License
This project is licensed under the MIT License - see the LICENSE file for details.
