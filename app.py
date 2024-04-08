from flask import Flask, request
import requests
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)

# Define the permitted sources as a list of URLs
PERMITTED_SOURCES = os.getenv('PERMITTED_SOURCES', '').split(',')

def fetch_channel_info(channel_id):
    url = f'{PERMITTED_SOURCES[0]}/api/v1/channels/{channel_id}'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Error fetching channel info: {e}")
        return None
    
def format_duration(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def create_podcast_feed(response_text, type_param, channel_info):
    root = ET.fromstring(response_text)
    rss = ET.Element('rss', {'version': '2.0', 'xmlns:itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd', 'xmlns:atom': 'http://www.w3.org/2005/Atom'})
    channel = ET.SubElement(rss, 'channel')

    title = channel_info.get('author', 'Default Author')
    description = channel_info.get('description', '')
    link = channel_info.get('authorUrl', '')
    image_url = channel_info.get('authorThumbnails')[5].get('url')
    author = channel_info.get('author', 'Default Author')

    ET.SubElement(channel, 'title').text = title
    ET.SubElement(channel, 'description').text = description
    ET.SubElement(channel, 'link').text = link

    image_elem = ET.SubElement(channel, 'image')
    ET.SubElement(image_elem, 'url').text = image_url
    ET.SubElement(image_elem, 'title').text = title
    ET.SubElement(image_elem, 'link').text = link

    ET.SubElement(channel, 'generator').text = 'api'
    ET.SubElement(channel, 'author').text = author

    itunes_explicit = 'No'
    is_family_friendly = channel_info.get('isFamilyFriendly', False)
    itunes_explicit = 'No' if is_family_friendly else 'Yes'
    ET.SubElement(channel, 'itunes:explicit').text = itunes_explicit

    ET.SubElement(channel, 'itunes:image', href=image_url)

    for video in channel_info['latestVideos']:
        title = video.get('title', 'Untitled Video')
        description = video.get('description', '')
        video_id = video.get('videoId', '')
        author = video.get('author', 'Default Author')
        published_text = video.get('publishedText', '')
        length_seconds = video.get('lengthSeconds', 0)
        itunes_duration = format_duration(length_seconds)
        
        item = ET.SubElement(channel, 'item')
        if type_param == 'audio':
            modified_url = f'{PERMITTED_SOURCES[0]}/latest_version?id={video_id}&itag=599'
            enclosure_type = 'audio/m4a'
        else:
            modified_url = f'{PERMITTED_SOURCES[0]}/latest_version?id={video_id}&itag=22'
            enclosure_type = 'video/mp4'
        
        ET.SubElement(item, 'title').text = title
        ET.SubElement(item, 'description').text = description
        ET.SubElement(item, 'link').text = link
        ET.SubElement(item, 'itunes:author').text = author
        ET.SubElement(item, 'itunes:summary').text = description
        ET.SubElement(item, 'itunes:duration').text = itunes_duration
        ET.SubElement(item, 'enclosure', {'url': modified_url, 'length': str(length_seconds), 'type': enclosure_type})
        ET.SubElement(item, 'guid', {'isPermaLink': 'false'}).text = f'https://www.youtube.com/watch?v={video_id}'
        ET.SubElement(item, 'pubDate').text = published_text
        ET.SubElement(item, 'itunes:image', {'href': video['videoThumbnails'][0]['url']})
        ET.SubElement(item, 'itunes:episodeType').text = enclosure_type

    rss_str = ET.tostring(rss, encoding='utf-8').decode('utf-8')
    return rss_str


@app.route('/podcast', methods=['GET'])
def handle_podcast_request():
    channel_id = request.args.get('channelId')
    type_param = request.args.get('type', 'video')

    if not channel_id:
        return 'Error: Channel ID is required.', 400

    channel_info = fetch_channel_info(channel_id)
    if not channel_info:
        return 'Error: Unable to fetch channel information.', 500

    permitted_source = PERMITTED_SOURCES[0] if PERMITTED_SOURCES else ''
    url = f'{permitted_source}/feed/channel/{channel_id}'

    try:
        response = requests.get(url)
        if response.status_code == 200:
            podcast_feed = create_podcast_feed(response.text, type_param, channel_info)
            return podcast_feed, {'Content-Type': 'application/xml'}
        else:
            return f'Error: Unable to fetch data from the URL. Status code: {response.status_code}', response.status_code
    except Exception as e:
        return f'Error: {str(e)}', 500


if __name__ == '__main__':
    app.run(port=5895)

