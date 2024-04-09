from flask import Flask, request, abort
import requests
import xml.etree.ElementTree as ET
import os
from datetime import datetime

app = Flask(__name__)

# Define the permitted sources as a list of URLs
PERMITTED_SOURCES = os.getenv('PERMITTED_SOURCES', 'https://inv.tux.pizza').split(',')

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
    # Parse the XML content
    root = ET.fromstring(response_text)

    # Define the namespace if present in the XML
    namespace = {
        'atom': 'http://www.w3.org/2005/Atom',
        'yt': 'http://www.youtube.com/xml/schemas/2015',
        'media': 'http://search.yahoo.com/mrss/',
        'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd',
        'dc': 'http://purl.org/dc/elements/1.1/'
    }

    # Create the RSS root element with iTunes and atom namespaces
    rss = ET.Element('rss', {'version': '2.0', 'xmlns:itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd', 'xmlns:atom': 'http://www.w3.org/2005/Atom'})
    channel = ET.SubElement(rss, 'channel')

    # Extract channel information
    title = channel_info.get('author', 'Default Author')  # Use a default author if not available
    description = channel_info.get('description', '')  # Use a default author if not available
    link = channel_info.get('authorUrl', '')
    image_url = channel_info.get('authorThumbnails')[5].get('url')
    generator = 'api'
    last_build_date = 'Your Last Build Date'
    author = channel_info.get('author', 'Default Author')  # Use a default author if not available
    #language = 'en-US' #root.find('.//atom:xml:lang', namespace).text  # Example language / #copyright = 'Your Copyright'

    # Add channel elements without namespace prefixes
    ET.SubElement(channel, 'title').text = title
    ET.SubElement(channel, 'description').text = description
    ET.SubElement(channel, 'link').text = link

    # Add image element
    image_elem = ET.SubElement(channel, 'image')
    ET.SubElement(image_elem, 'url').text = image_url
    ET.SubElement(image_elem, 'title').text = title
    ET.SubElement(image_elem, 'link').text = link

    ET.SubElement(channel, 'generator').text = generator
    ET.SubElement(channel, 'author').text = author
    #ET.SubElement(channel, 'copyright').text = copyright / ET.SubElement(channel, 'language').text = language /    ET.SubElement(channel, '{http://www.w3.org/2005/Atom}link', {'rel': 'hub', 'href': 'Your Hub Link'})

    # Add iTunes-specific tags
    itunes_explicit = 'No'
    itunes_category_text = 'Your iTunes Category Text'
    itunes_image_href = image_url
    ET.SubElement(channel, 'itunes:author').text = author
    ET.SubElement(channel, 'itunes:summary').text = description
    itunes_owner = ET.SubElement(channel, 'itunes:owner')
    ET.SubElement(itunes_owner, 'itunes:name').text = title
    # Dynamically set itunes_explicit based on isFamilyFriendly value
    is_family_friendly = channel_info.get('isFamilyFriendly', False)
    itunes_explicit = 'No' if is_family_friendly else 'Yes'
    ET.SubElement(channel, 'itunes:explicit').text = itunes_explicit
    #itunes_category = ET.SubElement(channel, 'itunes:category') /itunes_category.set('text', itunes_category_text) / sub_category = ET.SubElement(itunes_category, 'itunes:category') / sub_category.set('text', 'Your Subcategory Text')

    ET.SubElement(channel, 'itunes:image', href=itunes_image_href)

    # Extract and add episodes

     # Extract and add episodes
    for video in channel_info['latestVideos']:
        title = video.get('title', 'Untitled Video')
        description = video.get('description', '')
        video_id = video.get('videoId', '')
        author = video.get('author', 'Default Author')
        author_id = video.get('authorId', '')
        author_url = video.get('authorUrl', '')
        published = video.get('published', 0)
        published_text = video.get('publishedText', '')
        length_seconds = video.get('lengthSeconds', 0)
        # Format duration to HH:MM:SS
        itunes_duration = format_duration(length_seconds)
        # Add episode item with iTunes-specific tags
        item = ET.SubElement(channel, 'item')
        # Modify the video URL based on the type parameter
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
        #ET.SubElement(item, 'itunes:explicit').text = 'no'
        ET.SubElement(item, 'itunes:summary').text = description
        ET.SubElement(item, 'itunes:duration').text = itunes_duration
        ET.SubElement(item, 'enclosure', {'url': modified_url, 'length': str(length_seconds), 'type': enclosure_type})
        ET.SubElement(item, 'guid', {'isPermaLink': 'false'}).text = f'https://www.youtube.com/watch?v={video_id}'
        # Convert Unix timestamp to datetime object
        published_datetime = datetime.fromtimestamp(published)
        # Format the datetime object as a string in RFC 822 format (required for pubDate in RSS feeds)
        published_text = published_datetime.strftime('%a, %d %b %Y %H:%M:%S %z')
        ET.SubElement(item, 'pubDate').text = published_text
        ET.SubElement(item, 'itunes:image', {'href': video['videoThumbnails'][0]['url']})
        # Add other episode-specific elements based on your needs
        ET.SubElement(item, 'itunes:episodeType').text = enclosure_type

    # Convert the XML tree to string
    rss_str = ET.tostring(rss, encoding='utf-8').decode('utf-8')
    return rss_str



@app.route('/podcast', methods=['GET'])
def handle_podcast_request():
    channel_id = request.args.get('channelId')
    type_param = request.args.get('type', 'video')  # Default to 'video' if type is not specified

    if not channel_id:
        return 'Error: Channel ID is required.', 400
    
    # Fetch channel information using the API
    channel_info = fetch_channel_info(channel_id)
    if not channel_info:
        return 'Error: Unable to fetch channel information.', 500

    # Use the first permitted source in the list
    permitted_source = PERMITTED_SOURCES[0] if PERMITTED_SOURCES else ''

    # Construct the URL using the channel ID and permitted source
    url = f'{permitted_source}/feed/channel/{channel_id}'

    try:
        # Make a GET request to the URL
        response = requests.get(url)
        # Check if the request was successful
        if response.status_code == 200:
            # Create the podcast feed from the XML content
            podcast_feed = create_podcast_feed(response.text, type_param, channel_info)  # Pass channel_info here
            # Return the modified XML with correct content type
            return podcast_feed, {'Content-Type': 'application/xml'}
        else:
            return f'Error: Unable to fetch data from the URL. Status code: {response.status_code}', response.status_code
    except Exception as e:
        return f'Error: {str(e)}', 500


if __name__ == '__main__':
    app.run(port=5895)
