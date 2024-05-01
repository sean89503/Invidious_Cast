import xml.etree.ElementTree as ET
import os
from datetime import datetime
import time
import logging
import multiprocessing
from multiprocessing import Process
from app import app
from waitress import serve
import yt_dlp
import json


#########Set Peramiters
file_path = "channels.txt"
CAST_DOMAIN = os.getenv('CAST_DOMAIN')
if CAST_DOMAIN == None:
    CAST_DOMAIN = 'NEEDStoBEset'
CRON = os.getenv('CRON')
if CRON == None:
    CRON = 300
XML_DIRECTORY = os.path.join(os.getcwd(), 'xml_files')
logging.basicConfig(level=logging.INFO)
process_logger = logging.getLogger('ydl')
process_logger.setLevel(logging.ERROR)
########### START OF CRON APP

def update_health_status():
  global last_health_check_time
  last_health_check_time = time.time()

def get_channel_uploads(channel_id, max_videos):
    # Create yt_dlp options
    ydl_opts = {
        "quiet": True,  # Suppress output
        "no-warnings": True,  # Try to suppress warnings (might not work for all)        
        "ignoreerrors": True,  # Ignore download errors
        "extract_flat": True,  # Extract flat playlist
        "playlistend": max_videos,  # Limit the number of videos to retrieve
        "logger": process_logger,  # Custom logger to handle warnings        
    }
    # Create yt_dlp object
    ydl = yt_dlp.YoutubeDL(ydl_opts)   
    ogchannelid = channel_id
    try:
        # Get channel metadata
        channel_url = ''
        if channel_id.startswith('UC'):
             channel_id = channel_id.replace('UC', 'UU', 1)  # Replace at most once             
        if channel_id.startswith('UU'):
            channel_url = f'https://www.youtube.com/playlist?list={channel_id}'
        if channel_id.startswith('PLN'):
            channel_url = f'https://www.youtube.com/playlist?list={channel_id}'    
        if channel_id.startswith('RUMBLE'):
            channel_id = channel_id.replace('RUMBLE', '', 1)  # Replace at most once
            channel_url = f'https://rumble.com/c/{channel_id}'
        with ydl:
            channel_info = ydl.extract_info(channel_url, download=False)
            output_file = "channel_info.json"
            with open(output_file, "w") as json_file:
                json.dump(channel_info, json_file, indent=4)
            if channel_info is not None:
                if ogchannelid.startswith('UC'):
                    detailed_info = ydl.extract_info(f'https://www.youtube.com/channel/{ogchannelid}', download=False)
                    if detailed_info:
                        '''output_file = "channel_detail.json"
                        with open(output_file, "w") as json_file:
                            json.dump(detailed_info, json_file, indent=4)'''
                        # Extract URL from the first thumbnail or detailed view
                        thumbnails = detailed_info.get('thumbnails', [])
                        avatar_thumbnail = next((thumb for thumb in thumbnails if thumb.get('id') == 'avatar_uncropped'), None)
                        if avatar_thumbnail:
                            thumbnail_url = avatar_thumbnail.get('url')
                        else:
                            thumbnail_url = thumbnails[1].get('url', '')  # Default if no thumbnails found
                        channel_info['thumbnail_url'] = thumbnail_url
            output_file = "channel_uploads.json"
            with open(output_file, "w") as json_file:
                json.dump(channel_info, json_file, indent=4)
        # Check if channel_info is not None and contains videos
        if channel_info is not None:

            return channel_info
            #videos = [video for video in channel_info['entries'] if video.get('is_live') != True]
            #data = json.loads(videos)
            #return data
        else:
            print("Channel information not available or no videos found.")
            return []
    except yt_dlp.utils.DownloadError as e:
        print("Error:", e)
        return []

def fetch_all(channel_data, filter, limit):
    videos = []
    count = 0

    for video in channel_data['entries']:
        videoid = video.get('id')
        videoURL = video.get('url')
        if video.get('availability') is None:
            fetchdetail = fetch_video_info(videoURL)  # Assuming fetch_video_info is defined elsewhere
            if fetchdetail is not None:
                duration = fetchdetail.get('duration', 0)
                if duration !=0:
                    description = fetchdetail.get('description', '')
                    published = fetchdetail.get('pub_date', '')
                    thumbnail = fetchdetail.get('thumbnail', '')
                    webpage_url = fetchdetail.get('webpage_url', '')
                    if published:
                        pub_date = datetime.strptime(published, '%Y%m%d')
                        published_unix = int(pub_date.timestamp())
                        video['description'] = description
                        video['published'] = published_unix
                        video['duration'] = duration
                        video['thumbnail'] = thumbnail 
                        video['webpage_url'] = webpage_url
                        videos.append(video)
                        count += 1  # Increment count
                        if count == limit:
                            break  # Stop iterating if limit is reached



    return videos  # Return all processed videos

def fetch_video_info(videoURL):
      # Create yt_dlp options with custom logger
    ydl_opts = {
         "quiet": True,  # Suppress output
          "no-warnings": True,  # Try to suppress warnings (might not work for all)
          "logger": process_logger,  # Custom logger to handle warnings
                  }
    # Create yt_dlp object
    ydl = yt_dlp.YoutubeDL(ydl_opts)

    try:
        # Get video info
        with ydl:
            video_info = ydl.extract_info(videoURL, download=False)
            '''output_file = "videouploads.json"
            with open(output_file, "w") as json_file:
                    json.dump(video_info, json_file, indent=4)'''
        if video_info != None:
            return {
                'description': video_info.get('description', 'N/A'),
                'pub_date': video_info.get('upload_date', 'N/A'),
                'duration': video_info.get('duration', 'N/A'),
                'thumbnail': video_info.get('thumbnail', 'N/A'),
                'webpage_url': video_info.get('webpage_url', 'N/A'),
                }

    except yt_dlp.utils.DownloadError as e:
        print("Error:", e)
        return None

def format_published_date(unix_timestamp):
    # Convert Unix timestamp to datetime object
    dt_object = datetime.fromtimestamp(unix_timestamp)
    
    # Format the datetime object as a string in the desired format using strftime
    formatted_date = dt_object.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_date

def format_duration(seconds):
    # Convert total seconds to hours, minutes, and remaining seconds
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Format duration as HH:MM:SS
    formatted_duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return formatted_duration

def create_podcast_feed(type_param, channel_info, channel_id, filter, vidioquality, limit, latest):
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
    title = channel_info.get('title', 'Default Author') # Use a default author if not available
    # Check if the title starts with "Uploads from" and strip it if it does
    if title.startswith('Uploads from'):
        title = title[len('Uploads from'):].strip()
    pubDate = datetime.now()
    unixdate=  int(pubDate.timestamp())
    formatted_date = format_published_date(unixdate)
    description = channel_info.get('description', '') # Use a default author if not available
    authorId = channel_info.get('id', '')
    link = channel_info.get('channel_url', '')
    BACKUPIMAGE = channel_info.get('thumbnails')[1].get('url')
    image_url = channel_info.get('thumbnail_url',BACKUPIMAGE)
    generator = 'InvidiousCast'
    last_build_date = 'Your Last Build Date'
    author = channel_info.get('uploader', 'Default Author') # Use a default author if not available
    # Add channel elements without namespace prefixes
    ET.SubElement(channel, 'title').text = title
    ET.SubElement(channel, 'pubDate').text = formatted_date
    ET.SubElement(channel, 'generator').text = 'InvidiousCast'
    #ET.SubElement(channel, 'podcast:locked').text = 'yes'
    ET.SubElement(channel, 'link').text = link
    ET.SubElement(channel, 'language').text = 'English'
    ET.SubElement(channel, 'copyright').text = description
    ET.SubElement(channel, 'description').text = author
    ET.SubElement(channel, 'docs').text = 'google.com'
    ET.SubElement(channel, 'managingEditor').text = 'invidiouscast@example.com'
        # Add image element
    image_elem = ET.SubElement(channel, 'image')
    ET.SubElement(image_elem, 'url').text = image_url
    # Add iTunes-specific tags
    itunes_explicit = 'No'
    itunes_image_href = image_url
    itunes_owner = ET.SubElement(channel, 'itunes:owner')
    is_family_friendly = channel_info.get('isFamilyFriendly', False)
    itunes_explicit = 'No' if is_family_friendly else 'Yes'
    ET.SubElement(channel, 'itunes:summary').text = description
    ET.SubElement(channel, 'itunes:author').text = author
    ET.SubElement(channel, 'itunes:keyword').text = ''
    ET.SubElement(channel, 'itunes:category').text = 'TV & Film'
    ET.SubElement(channel, 'itunes:image', href=itunes_image_href)
    ET.SubElement(channel, 'itunes:explicit').text = itunes_explicit
    ET.SubElement(channel, 'itunes:owner').text = ''
    ET.SubElement(itunes_owner, 'itunes:name').text = title
    ET.SubElement(itunes_owner, 'itunes:email').text = 'invidiouscast@example.com'
    ET.SubElement(channel, 'itunes:block').text = 'yes'
    ET.SubElement(channel, 'itunes:type').text = 'episodic'
    # Extract and add episodes
    logging.info(f'Creating feed for {authorId}({author}), type:{type_param}, limit:{limit}, filter: {filter}')
    for video in latest:
        video_id = video.get('id', '') 
        title = video.get('title', 'Untitled Video')
        pubfromvid = video.get('published')
        formatted_date = format_published_date(pubfromvid)
        length_seconds = video.get('duration', 0)
        itunes_duration = format_duration(length_seconds)
        linkbackup = f'https://www.youtube.com/watch?v={video_id}'
        videolink = video.get('webpage_url', linkbackup)
        description = video.get('description', 'error')
        description = f"{description}\nLink: {videolink}"
        thumbnail_urlbackup = f'https://i3.ytimg.com/vi/{video_id}/maxresdefault.jpg'
        thumbnail_url = video.get('thumbnail', thumbnail_urlbackup)        
        modified_url = f'{CAST_DOMAIN}/url?id={video_id}&type={type_param}'
        if type_param == 'audio':             
            enclosure_type = 'audio/m4a'
        else:
          enclosure_type = 'video/mp4'
        item = ET.SubElement(channel, 'item')       
        ET.SubElement(item, 'title').text = title
        ET.SubElement(item, 'itunes:title').text = title
        ET.SubElement(item, 'pubDate').text = formatted_date
        ET.SubElement(item, 'guid', {'isPermaLink': 'false'}).text = f'{videolink}'
        ET.SubElement(item, 'link').text = videolink
        ET.SubElement(item, 'description').text = description
        ET.SubElement(item, 'enclosure', {'url': modified_url, 'length': str(length_seconds), 'type': enclosure_type})
        ET.SubElement(item, 'itunes:duration').text = itunes_duration
        ET.SubElement(item, 'itunes:explicit').text = 'false'
        ET.SubElement(item, 'itunes:block').text = 'yes'
        ET.SubElement(item, 'itunes:subtitle').text = description
        ET.SubElement(item, 'itunes:episodeType').text = 'full'
        ET.SubElement(item, 'itunes:author').text = author
        ET.SubElement(item, 'itunes:image', {'href': thumbnail_url})
    # Convert the XML tree to string
    rss_str = ET.tostring(rss, encoding='utf-8').decode('utf-8')
    #print('Found videos')
    return rss_str

def handle_podcast_request(channel_id, channel_type, channel_limit, filter, latest, channel_data):
    vidioquality = '720p'  # Default video quality
    # Check if the XML directory exists
    if not os.path.exists(XML_DIRECTORY):
        try:
            os.makedirs(XML_DIRECTORY)
        except OSError as e:
            print(f"Error creating directory: {e}")
            return None
   # Fetch channel information using the API
    channel_info = channel_data #fetch_channel_info(channel_id)
    if not channel_info:
        return 'Error: Unable to fetch channel information.', 500
    else:
        # Create the podcast feed from the XML content
        podcast_feed = create_podcast_feed( channel_type, channel_info, channel_id, filter, vidioquality, channel_limit, latest)
        # Save the XML content to a file in the XML directory
            
        if not os.path.exists(XML_DIRECTORY):
            os.makedirs(XML_DIRECTORY)
        filename = f'{channel_id}.xml'
        filepath = os.path.join(XML_DIRECTORY, filename)
        #print(f'saving to xml')
        with open(filepath, 'w', encoding='utf-8') as xml_file:
                xml_file.write(podcast_feed)
                print('saved')
                return podcast_feed

            # Return the modified XML with correct content type
            #return podcast_feed, {'Content-Type': 'application/xml'}

        #else:
            #return f'Error: Unable to fetch data from the URL. Status code: {response.status_code}', response.status_code

def read_channel_ids_from_file(file_path, max_retries=5):
    print('...............................................................................................................')
    print('######..##..##..##..##..######..#####...######...####...##..##...####............####....####....####...######.',)
    print('..##....##..##..##..##....##....##..##....##....##..##..##..##..##..............##..##..##..##..##........##...',)
    print('..##....##.###..##..##....##....##..##....##....##..##..##..##...####...........##......######...####.....##...',)
    print('..##....##..##...####.....##....##..##....##....##..##..##..##......##..........##..##..##..##......##....##...',)
    print('######..##..##....##....######..#####...######...####....####....####............####...##..##...####.....##...',)
    print('...............................................................................................................',)
    """
    Reads channel IDs and information from a file.
    Args:
        file_path (str): The path to the file containing channel data.
        max_retries (int, optional): The maximum number of times to retry waiting for the file to exist. Defaults to 5.
    Returns:
        list or None: If the file exists and is valid, returns a list of channel data.
    """
    while True:  # Run indefinitely in a loop
    # Wait for file to exist with a timeout
        for attempt in range(max_retries):
          if os.path.exists(file_path):
            break
          logging.warning(f"Waiting for file '{file_path}' to be available... (Attempt {attempt + 1}/{max_retries})")
          time.sleep(5)
        else:
          logging.error("File not found after retries: {}".format(file_path))
          return None
        try:
            with open(file_path, 'r') as file:
                logging.info('Looking at subscriptions...') 
                for line in file.read().splitlines():
                    update_health_status()
                    parts = line.strip().split(':')
                    channel_id = parts[0]
                    channel_type = parts[1].lower() if len(parts) > 1 else 'video'
                    limit = int(parts[2]) if len(parts) > 2 else 5                        
                    filter = parts[3].lower() if len(parts) > 2 else  'none'  
                    if channel_id == '':
                        logging.error(f'error on grabbing line in channels.txt check if blank line')   
                        continue  # Skip processing this line and move to the next one
                    if channel_id.startswith('@'):  #if a user puts in the @userid for youtube it will grab the channelid of the user
                        ydl_opts = {
                            "quiet": True,  # Suppress output
                            "ignoreerrors": True,  # Ignore download errors
                            "extract_flat": True,  # Extract flat playlist
                            "playlistend": 1,  # Limit the number of videos to retrieve
                        }
                        # Create yt_dlp object
                        ydl = yt_dlp.YoutubeDL(ydl_opts)   
                        try:
                            channel_url = f'https://www.youtube.com/{channel_id}'
                            with ydl:
                                channel_info = ydl.extract_info(channel_url, download=False)
                            channel_id = channel_info.get('channel_id')
                        except yt_dlp.utils.DownloadError as e:
                             logging.error('Error in making podcastfeed')
                             continue
                    channel_data = get_channel_uploads(channel_id, limit)
                    title = channel_data.get('title')
                    # Check if the title starts with "Uploads from" and strip it if it does
                    if title.startswith('Uploads from'):
                        title = title[len('Uploads from'):].strip()
                    chlatest = fetch_all(channel_data, filter,1)
                    if chlatest is not None: 
                        if len(chlatest) > 0:
                            video_id = chlatest[0]['id']
                        else:
                            print(f"No videos found for {title} ")                
                    else: 
                        logging.error(f'error on grabbing chlatest for {title} ({channel_id})')   
                        return None 
                    xmllatest = find_latest_video(channel_id)

                    if video_id != xmllatest:
                        if xmllatest == 'nofile':
                            logging.info(f'Found new feed item {title} ({channel_id})')
                            print(f'Found new feed item {title} ({channel_id})')
                        else:
                            logging.info(f'Found new videos ({video_id}) only have {xmllatest} on {title} ({channel_id})')
                            print(f'Found new videos ({video_id}) only have {xmllatest} on {title} ({channel_id})')
                        chlatest = fetch_all(channel_data, filter, limit)
                        latest = chlatest 
                        complete = handle_podcast_request(channel_id, channel_type, limit, filter, latest, channel_data)
                        time.sleep(.2)
                        logging.info(f'Done updating {title} ({channel_id})') 
                        print(f'Done updating {title} ({channel_id})') 
                        if complete is None:
                            logging.error('Error in making podcastfeed')
                            return None
                    else:
                        logging.info(f'Done Checking {title} ({channel_id})') 
        except ValueError:
            logging.warning(f"Invalid channel type '{channel_type}' for channel {title} ")
        logging.info(f'Finished round of lookups. Will look agian in f{CRON} seconds ') 
        time.sleep(CRON)  # Delay for 60 seconds before checking the file again

def find_latest_video(filename):
  """
  Extracts the first video ID from a specified XML file.
  Args:
      filename (str): The filename (including the '.xml' extension).
  Returns:
      str: The first video ID found in the XML file, or None if no video is found or errors occur.
  """
  try:
    # Construct the full filepath using XML_DIRECTORY and filename
    filepath = os.path.join(XML_DIRECTORY, filename)
    filepath = f'{filepath}.xml'
    if os.path.exists(file_path):  
        # Read the XML content from the file
        with open(filepath, 'rb') as f:
          xml_content = f.read()

        # Parse the XML content (modify if content is a string)
        if isinstance(xml_content, bytes):
          root = ET.fromstring(xml_content)
        else:
          root = ET.fromstring(xml_content.encode('utf-8'))

        # Find the first child element named 'item' under the 'channel' element
        item_element = root.find('channel/item')

        if item_element is None:
          return None

        # Find the first child element named 'enclosure' under the 'item' element
        enclosure_element = item_element.find('enclosure')

        if enclosure_element is None:
          return None

        # Extract the video ID from the enclosure URL (assuming specific format)
        enclosure_url = enclosure_element.get('url')
        if not enclosure_url:
          return None

        video_id_parts = enclosure_url.split('=')
        if len(video_id_parts) > 1:
          return video_id_parts[1].split('&')[0]
        else:
          return None
    else:
        return 'hhhhd'
      
  except Exception as e:
    return 'nofile'
  
def worker(queue):
    while True:
        task = queue.get()
        if task is None:
            break
        print(f"Processing task {task}")
        # Perform data processing on the task (e.g., calculations, transformations)
        result = task * 2  # Example data processing operation
        print(f"Processed task result: {result}")
        time.sleep(1)  # Simulate processing time
 
  
def run_with_workers(port, num_workers, queue):
    # Create and start worker processes
    processes = [Process(target=worker, args=(queue,)) for _ in range(num_workers)]
    for process in processes:
        process.start()

    # Serve the Flask app with Waitress
    serve(app, host='0.0.0.0', port=port)

if __name__ == '__main__':
    # Create a multiprocessing Queue
    queue = multiprocessing.Queue()

    def start_link_updater(file_path):
        process = Process(target=read_channel_ids_from_file, args=(file_path,))
        process.daemon = True
        process.start() 

    start_link_updater(file_path)
    run_with_workers(5895,12, queue)
      
