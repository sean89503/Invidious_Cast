

![invidious_Cast logo](https://github.com/sean89503/Invidious_Cast/blob/main/logo.png?raw=true)


# Invidious Cast

Invidious Cast is a Flask application that generates RSS feeds for podcasts based on YouTube channels. It allows you to customize the podcast feed format and includes support for iTunes-specific tags.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
  - [Using Docker](#using-docker)
  - [Using Windows](#using-windows)
- [Known Issues](#known-issues)
- [Contributing](#contributing)
- [License](#license)
- [Roadmap](#roadmap)
- [Contributors](#contributors)

## Features
- Convert YouTube channel or Youtube playlist content into podcast RSS feeds.
- No API needed
- Support for audio and video formats with customizable URLs.
- Automatic handling of iTunes-specific tags for improved compatibility.
- Thumbnail art support.
- Blocking to prevent your feed from being listed.
- Link to the source video added to the end of the description.
- Only add videos that are available (no scheduled lives or geoblocked).

## Installation
Create a `channels.txt` file. Please look at the example format:
- ChannelID/Playlist: is case sensitive
- Type: video or audio (default is video)
- Limit: number of videos to put in feed (default is 5)
- Filter: used to filter out video types (such as shorts and lives) (default is none)

Example lines:

```txt
UCMLSTcLBdfdsMQ0TfzQzUIw:video:3:none
UCMLSTcLB4HefgdfgfzQzUIw:audio:20:none
@TheInvidiousCast:video:5:none
```
or if you want to use defualts it can look like
```txt
UCMLSTcLBdfdsMQ0TfzQzUIw
UCMLSTcLB4HefgdfgfzQzUIw
@TheInvidiousCast
```
each line must have the channel id and i one peramiter is needed please fill out all so it will know what permiter it is refuring 

### Using Docker
1. Clone the repository:
   ```cmd
   git clone https://github.com/sean89503/Invidious_Cast.git
   ```
2. Navigate into created folder:
  ```cmd
  cd Invidious_Cast
  ```
3. Build a Docker Image
  ```cmd
  sudo docker build -t invidiouscast .
  ```
4. Run Container 
  ```cmd
  sudo docker run -d \
  --name invidiouscast \
  -e CAST_DOMAIN=https://YOURDOMAINTOINVIDIOUSCAST \
  -e CRON=300 \
  -p 5895:5895 \
  -v /HOST/Docker/invidious-cast/xml_files:/app/xml_files:rw \
  -v /HOST/Docker/invidious-cast/channels.txt:/app/channels.txt:rw \
  -v /HOST/invidious-cast/templates:/app/templates:rw \
  --restart unless-stopped \
  invidiouscast
```
   make sure you add your 'CAST_DOMAIN' URL example "https://invidiouscast.example.com" this is were you want to host it. .
   Map the volumes yo were you can access them. the app could run without you having access but it is easer to trublshout and manahe the channels file without     having to access the container.
  
## Using Windows
### 1. Copy Files

Copy the following files and folders to your desired location:
- `main.py`
- `app.py`
- `requirments.txt`
- `Template` folder (contains HTML templates for your app)

### 2. Set Environment Variables

1. Open Command Prompt (CMD) as an administrator.
2. Set the `CAST_DOMAIN` variable:

   ```cmd
   set CAST_DOMAIN=https://yourcastdomain.com
   ```
3. Set the `CRON` variable (time in seconds between checks for new episodes):
   ```cmd
   set CRON=300
   ```
 
### 3. Install Requirements

1. Navigate to the directory where your files are located.
2. Install the required packages:
   ```cmd
   pip install -r requirements.txt
   ```

### 4. Prepare channels.txt

Ensure that the `channels.txt` file is in the same directory as `main.py` and `app.py`. This file should follow the specified format for listing channel IDs or playlists.

### 5. Start the Application

Run the following command to start your application:
  ```cmd
  python main.py
  ```
  If you want to run it at a service I would use [nssm](https://nssm.cc/)

## Post Instalation
### 1.
  Pount your domain to invidious_cast 
  I use and suggest [clouflaried tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) 
   
### 2.
   After a full run
   Go to `https://yourdomain.com/`  << This will show you all the xml files
   now try `https://yourdomain.com/opml` << this will help you create an opml url for importing into your podcast manager
   
   ![image](https://github.com/sean89503/Invidious_Cast/assets/22017525/3e3bfe15-a9ec-4978-9536-f00a7f51900d)

## Known Issues
  - filter peramiter is not working

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
  waitress: https://github.com/Pylons/waitress
  Flask: https://flask.palletsprojects.com/
  xml.etree.ElementTree: https://docs.python.org/3/library/xml.etree.elementtree.html

Release History
  1.0.0 - Initial release: 4/8/2024
  2.0.0 - Rewrote to use yt-dlp
  
  Invidious Cast is not affiliated with or endorsed by YouTube or iTunes. This is an independent project for creating podcast RSS feeds from YouTube content.

## Roadmap
  - add support for filtering shorts, lives and shows
  - improve logic for geo-blocked videos
  - ability to add/remove subscription from browser
  - Add support for more customization options in the RSS feed.
  - Improve error handling and logging.
  - Enhance performance for large YouTube channels.
  - Support for more services

## Contributors
(@sean89503 )
We welcome contributions from the community. If you'd like to contribute, please follow the Contributing guidelines.
