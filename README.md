

![invidious_Cast logo](https://github.com/sean89503/Invidious_Cast/blob/main/logo.png?raw=true)


# Invidious Cast

Invidious Cast is a Flask application that generates RSS feeds for podcasts based on YouTube channels. It allows you to customize the podcast feed format and includes support for iTunes-specific tags.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
  - [Using Docker](#using-docker)
- [Usage](#usage)
- [Configuration](#configuration)
- [Known Issues](#issues)
- [Contributing](#contributing)
- [License](#license)
- [Roadmap](#roadmap)
- [Contributors](#contributors)

## Features

- Convert YouTube channel content into podcast RSS feeds.
- Support for audio and video formats with customizable URLs.
- Automatic handling of iTunes-specific tags for improved compatibility.

## Installation

### Using Docker

1. Clone the repository:
   ```cmd
   git clone https://github.com/sean89503/Invidious_Cast.git
   ```
2. Navigate into created folder:
  ```cmd
  cd invidious-cast
  ```
3. Build a Docker Image
  ```cmd
  sudo docker build -t invidiouscast .
  ```
4. Run Container 
  ```cmd
  sudo docker run -e PERMITTED_SOURCES="???" -p 5895:5895 --name invidiouscast invidiouscast
```
   make sure you add your invidious source URL(s) example "https://invidious.example.com" you can add multable sources like "https://invidious.example1.com,https://invidious.example2.com". The script will see if the channel is on the first listed source and if it can't find it it will move to the next.
   
5. Try it out
got to DOCKER_IP:5898/podcast?channelId=CHANNEL_ID << this will get you a video 
or try DOCKER_IP:5898/podcast?channelId=CHANNEL_ID&type=audio << this will get you audio 



## Contributing
Fork the repository.
Create a new branch (git checkout -b feature/improvement).
Make your changes.
Commit your changes (git commit -am 'Add new feature').
Push to the branch (git push origin feature/improvement).
Create a new Pull Request.
Please follow our Code of Conduct in all interactions.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

Support
For any questions or issues, please open an issue on GitHub.

Acknowledgments
This project uses the following libraries:

Flask: https://flask.palletsprojects.com/
Requests: https://docs.python-requests.org/
xml.etree.ElementTree: https://docs.python.org/3/library/xml.etree.elementtree.html
Release History
1.0.0
Initial release: 4/8/2024

Invidious Cast is not affiliated with or endorsed by YouTube or iTunes. This is an independent project for creating podcast RSS feeds from YouTube content.

## Roadmap
add support for shorts
add support for live videos 
Add support for more customization options in the RSS feed.
Improve error handling and logging.
Enhance performance for large YouTube channels.

## Contributors
(@sean89503 )
We welcome contributions from the community. If you'd like to contribute, please follow the Contributing guidelines.
