
from flask import Flask, request, abort
import requests
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)

# Define the permitted sources as a list of URLs
PERMITTED_SOURCES = os.getenv('PERMITTED_SOURCES', 'https://inv.tux.pizza').split(',')

def create_podcast_feed(response_text, type_param):
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
    title = root.find('.//atom:title', namespace).text
    description = title  # Default description
    link = root.find('.//atom:link[@rel="alternate"]', namespace).attrib['href']
    image_url = root.find('.//atom:icon', namespace).text
    generator = 'invidious_cast'
    last_build_date = 'Your Last Build Date'
    author = root.find('.//atom:author/atom:name', namespace).text
    copyright = 'Your Copyright'
    language = 'en-US' #root.find('.//atom:xml:lang', namespace).text  # Example language
    image = root.find('.//atom:icon', namespace).text

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
    #ET.SubElement(channel, 'lastBuildDate').text = last_build_date
    #ET.SubElement(channel, '{http://www.w3.org/2005/Atom}link', {'href': 'Your Atom Link', 'rel': 'self', 'type': 'application/rss+xml'})
    ET.SubElement(channel, 'author').text = author
    #ET.SubElement(channel, 'copyright').text = copyright
    ET.SubElement(channel, 'language').text = language
    ET.SubElement(channel, '{http://www.w3.org/2005/Atom}link', {'rel': 'hub', 'href': 'Your Hub Link'})

    # Add iTunes-specific tags
    itunes_author = author
    itunes_summary = description
    itunes_type = 'Your iTunes Type'
    itunes_owner_name = title
    itunes_owner_email = 'Your iTunes Owner Email'
    itunes_explicit = 'No'
    itunes_category_text = 'Your iTunes Category Text'
    itunes_image_href = image_url

    ET.SubElement(channel, 'itunes:author').text = itunes_author
    ET.SubElement(channel, 'itunes:summary').text = itunes_summary
    #ET.SubElement(channel, 'itunes:type').text = itunes_type

    itunes_owner = ET.SubElement(channel, 'itunes:owner')
    ET.SubElement(itunes_owner, 'itunes:name').text = itunes_owner_name
    #ET.SubElement(itunes_owner, 'itunes:email').text = itunes_owner_email

    ET.SubElement(channel, 'itunes:explicit').text = itunes_explicit

    #itunes_category = ET.SubElement(channel, 'itunes:category')
    #itunes_category.set('text', itunes_category_text)
    #sub_category = ET.SubElement(itunes_category, 'itunes:category')
    #sub_category.set('text', 'Your Subcategory Text')

    ET.SubElement(channel, 'itunes:image', href=itunes_image_href)

    # Extract and add episodes
    entries = root.findall('.//atom:entry', namespace)
    for entry in entries:
        title = entry.find('atom:title', namespace).text
        description = entry.find('.//media:description', namespace).text  # Extract description from media:description if available
        link = entry.find('atom:link[@rel="alternate"]', namespace).attrib['href']
        video_id = entry.find('yt:videoId', namespace).text
        guid = 'Your GUID'
        creator = author
        pub_date = entry.find('atom:published', namespace).text

        enclosure_length = 'Your Enclosure Length'
        #enclosure_type = 'Your Enclosure Type'
        itunes_summary = description
        itunes_explicit = 'Your iTunes Explicit for Episode'
        itunes_duration = 'Your iTunes Duration'
        #itunes_image_href = 'Your iTunes Image Href for Episode'
        itunes_episode = 'Your iTunes Episode'

        # Get episode artwork URL
        itunes_image_href = entry.find('.//media:thumbnail', namespace).attrib['url']
        # Modify the video URL based on the type parameter
        if type_param == 'audio':
            modified_url = f'{PERMITTED_SOURCES[0]}/latest_version?id={video_id}&itag=599'
            enclosure_type = 'audio/m4a'
        else:
            modified_url = f'{PERMITTED_SOURCES[0]}/latest_version?id={video_id}&itag=22'
            enclosure_type = 'video/mp4'
        itunes_episode_type = enclosure_type
        enclosure_url = modified_url
        '''
        # Check if the modified URL works, if not, try other permitted sources -slowed it down
        try:
            response = requests.head(enclosure_url)
            if response.status_code != 200:
                if type_param == 'audio':
                    for source in PERMITTED_SOURCES:
                        modified_url = f'{source}/latest_version?id={video_id}&itag=599'  # Try audio/weba
                        enclosure_url = modified_url
                        response = requests.head(enclosure_url)
                        if response.status_code == 200:
                            enclosure_type = 'audio/m4a'
                            break
                else:
                    for source in PERMITTED_SOURCES:
                        modified_url = f'{source}/latest_version?id={video_id}&itag=22'  # Try video/mp4
                        enclosure_url = modified_url
                        response = requests.head(enclosure_url)
                        if response.status_code == 200:
                            enclosure_type = 'video/mp4'
                            break
        except Exception as e:
            print(f"Error checking URL: {e}")
        '''

        # Create episode item with iTunes-specific tags
        item = ET.SubElement(channel, 'item')
        ET.SubElement(item, 'title').text = title
        ET.SubElement(item, 'description').text = description
        ET.SubElement(item, 'link').text = link
        #ET.SubElement(item, 'guid', {'isPermaLink': 'false'}).text = guid
        ET.SubElement(item, 'creator').text = creator
        ET.SubElement(item, 'pubDate').text = pub_date
        ET.SubElement(item, 'enclosure', {'url': enclosure_url, 'type': enclosure_type})
        ET.SubElement(item, 'itunes:summary').text = itunes_summary
        #ET.SubElement(item, 'itunes:explicit').text = itunes_explicit
        #ET.SubElement(item, 'itunes:duration').text = itunes_duration
        ET.SubElement(item, 'itunes:image', href=itunes_image_href)
        #ET.SubElement(item, 'itunes:episode').text = itunes_episode
        ET.SubElement(item, 'itunes:episodeType').text = itunes_episode_type

    # Convert the XML tree to string
    rss_str = ET.tostring(rss, encoding='utf-8').decode('utf-8')
    return rss_str



@app.route('/podcast', methods=['GET'])
def handle_podcast_request():
    channel_id = request.args.get('channelId')
    type_param = request.args.get('type', 'video')  # Default to 'video' if type is not specified

    if not channel_id:
        return 'Error: Channel ID is required.', 400
    
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
            podcast_feed = create_podcast_feed(response.text, type_param)
            # Return the modified XML with correct content type
            return podcast_feed, {'Content-Type': 'application/xml'}
        else:
            return f'Error: Unable to fetch data from the URL. Status code: {response.status_code}', response.status_code
    except Exception as e:
        return f'Error: {str(e)}', 500

if __name__ == '__main__':
    app.run(port=5895)