from flask import Flask, request, send_from_directory, render_template, redirect, flash, Response
import requests
import xml.etree.ElementTree as ET
import os
from datetime import datetime
import time
import logging
from multiprocessing import Process
import yt_dlp

app = Flask(__name__)

#########Set Peramiters
file_path = "channels.txt"
PERMITTED_SOURCES = os.getenv('PERMITTED_SOURCES', 'https://yewtu.be,https://invidious.materialio.us,https://inv.tux.pizza,https://vid.puffyan.us,https://yewtu.be,https://iv.nboeck.de,https://yt.drgnz.club,https://iv.datura.network,https://invidious.fdn.fr,https://invidious.perennialte.ch,https://yt.artemislena.eu,https://invidious.flokinet.to,https://invidious.projectsegfau.lt,https://invidious.privacydev.net,https://iv.melmac.space,https://iv.ggtyler.dev,https://cal1.iv.ggtyler.dev,https://nyc1.iv.ggtyler.dev,https://invidious.lunar.icu,https://inv.nadeko.net,https://invidious.protokolla.fi').split(',')
XML_DIRECTORY = os.path.join(os.getcwd(), 'xml_files')
CAST_DOMAIN = os.getenv('CAST_DOMAIN')
logging.basicConfig(level=logging.INFO)
main_logger = logging.getLogger(__name__)
process_logger = logging.getLogger('cast')

def fetch_url(video_id, typed):
    # Define the video URL
    video_url = f'https://www.youtube.com/watch?v={video_id}'

    # Create yt_dlp options
    ydl_opts = {
        'quiet': True,  # Suppress output
    }

    # Create yt_dlp object
    ydl = yt_dlp.YoutubeDL(ydl_opts)

    try:
        # Get video info
        with ydl:
            video_info = ydl.extract_info(video_url, download=False)

        # Check if formats are available
        if 'formats' in video_info:
            # Filter formats to find the desired one (e.g., format ID '22' or '251')
            if typed == 'audio':
                format_id = '251'
            else:
                format_id = '22'  # Or use type or any specific logic to determine the format ID
            selected_format = next(
                (f for f in video_info['formats'] if f.get('format_id') == format_id), None
            )
            if selected_format:
                direct_url = selected_format['url']
                return direct_url
            else:
                print("Error: Desired format not found.")
        else:
            print("Error: No formats available for the video.")

    except yt_dlp.utils.DownloadError as e:
        print("Error:", e)
        # Handle the error condition if needed

#####START OF WEB APP ###############

@app.route('/url')
def url():
  video_id = request.args.get('id')
  typed = request.args.get('type')
  direct_url = fetch_url(video_id, typed)
  '''data = fetch_videos_info(video_id, 'max')
  time.sleep(10)
  for returnedvideo in data:
     video = returnedvideo.get('videodir')
     audio = returnedvideo.get('audiodir')     
  if  typed == 'audio':
     return redirect(f'{audio[0]}')
  if typed != 'audio':
     return redirect(f'{video[0]}')  
  '''
  if direct_url:
        return redirect(direct_url)
  else:
        return "Error: Failed to fetch the URL."

@app.route('/xml_files/<path:filename>')
def download_file(filename):
  return send_from_directory(XML_DIRECTORY, filename)

@app.route('/')
def list_files():
 files = [f for f in os.listdir(XML_DIRECTORY) if f.endswith('.xml')]
 file_links = ''.join([f'<a href="/xml_files/{filename}">{filename}</a><br>' for filename in files])
  
 # Add the HTML <img> tag for the logo
 logo_url = 'https://github.com/sean89503/Invidious_Cast/blob/main/logo.png?raw=true'
 logo_html = f'<img src="{logo_url}" alt="Logo" style="width: 100px; height: 100px;"><br>'
 return f'{logo_html}<h1>XML Files:</h1>{file_links}'

def generate_opml(files, domain):
 opml_content = '<?xml version="1.0" encoding="UTF-8"?><opml version="1.0">'
 for filename in files:
  filepath = os.path.join(XML_DIRECTORY, filename)
  if filename.endswith('.xml'):
   try:
    tree = ET.parse(filepath)
    root = tree.getroot()
    replacements = {'&': '&amp;', '-': '&#45;'}
    channel_title = root.find('channel/title').text.translate(str.maketrans(replacements)) if root.find('channel/title') is not None else ''
    # Include text attribute only if title exists
    outline_text = f'text="{channel_title}"' if channel_title else 'text="TEST"'
    opml_content += f'<outline type="rss" {outline_text} xmlUrl="{domain}/xml_files/{filename}" />'
    #opml_content += f'<outline xmlUrl="{domain}/xml_files/{filename}" />'
   except Exception as e:
    print(f"Error parsing {filename}: {e}")

 opml_content += '</opml>'
 return opml_content 

@app.route('/opml')
def get_opml():
  domain = request.args.get('domain')
  if domain == None:
    domain = CAST_DOMAIN
    if domain != None:
       return redirect(f'/opml?domain={domain}')
  print(f"Received domain: {domain}")  # Add this line
  if domain:
    files = [f for f in os.listdir(XML_DIRECTORY) if f.endswith('.xml')]
    opml_data = generate_opml(files, domain)
    return Response(opml_data, mimetype='text/xml')
  else:
    # Redirect to form if no domain submitted
    return redirect('/opml_form')

  files = [f for f in os.listdir(XML_DIRECTORY) if f.endswith('.xml')]
  opml_data = generate_opml(files, domain)
  return Response(opml_data, mimetype='text/xml')

@app.route('/opml_form')
def opml_form():
    return render_template('opml_form.html')

def remove_channel(channel_id):
    file_path = 'channels.txt'
    
    # Read existing channel data efficiently
    channels = []
    try:
        with open(file_path, 'r+') as f:
            lines = f.readlines()
            filtered_lines = [line for line in lines if not line.startswith(channel_id)]
            new_file_size = sum(len(line) for line in filtered_lines)
            f.seek(0)
            f.truncate(new_file_size)
            f.writelines(filtered_lines)

        # Remove blank lines from the file
        remove_blank_lines_from_file(file_path)

        # Remove XML file if it exists
        xml_filepath = os.path.join(XML_DIRECTORY, f'{channel_id}.xml')
        if os.path.exists(xml_filepath):
            os.remove(xml_filepath)

        return True
    except IOError as e:
        print(f"Error removing channel: {e}")
        return False

@app.route('/remove', methods=['GET', 'POST'])
def remove_channel_form():
    remote_addr = request.remote_addr
    print(f'ip return as {remote_addr}')
    if remote_addr == '127.0.0.1' or remote_addr.startswith('10.0.0.'):
        if request.method == 'POST':
            channel_id = request.form['channel_id']
            if remove_channel(channel_id):
                flash(f'Channel removed successfully (if it existed) from {remote_addr}.')
                time.sleep(3)
            else:
                flash('Failed to remove channel.')  # Use flash message for error
                time.sleep(3)
            return redirect('/')  # Redirect to OPML after removal 

    return render_template('remove_channel.html')

def has_text_in_last_line(filename):
  try:
    with open(filename, 'r') as f:
      lines = f.readlines()
      filtered_lines = [line for line in lines if line.strip() != '']
      if not lines:  # Handle empty file case
        return False
      if filtered_lines and not filtered_lines[-1].strip():
            filtered_lines.pop()  # Remove the last line (if empty)
      f.seek(0)
      f.truncate()
      f.writelines(filtered_lines)
  except IOError as e:
    print(f"Error opening file: {e}")
    return False  # Indicate error

def remove_blank_lines_from_file(file_path):
    try:
        with open(file_path, 'r+') as f:
            lines = f.readlines()
            filtered_lines = [line for line in lines if line.strip()]
            f.seek(0)
            f.truncate()
            f.writelines(filtered_lines)
            return True
    except IOError as e:
        print(f"Error opening or writing to file: {e}")
        return False

def is_file_empty(file_path):
    try:
        with open(file_path, 'r') as f:
            return not any(f)
    except IOError as e:
        print(f"Error opening file: {e}")
        return True

def process_form(channel_id, channel_type, channel_limit):
    # Validate channel ID (optional, customize validation as needed)
    if not channel_id:
        flash('Channel ID is required.')
        return False

    # Set default values for type and limit if empty
    channel_type = channel_type if channel_type else 'video'
    channel_limit = int(channel_limit) if channel_limit else 5
    file_path = 'channels.txt'

    if remove_blank_lines_from_file(file_path):
        if is_file_empty(file_path):
            with open(file_path, 'a') as f:
                f.write(f"{channel_id}:{channel_type}:{channel_limit}")  # Add without newline if empty
        else:
            with open(file_path, 'r+') as f:
                f.seek(0, 2)  # Move to the end of the file
                f.write(f"{channel_id}:{channel_type}:{channel_limit}")  # Add with newline if not empty
        
        flash(f'Channel "{channel_id}" (type: {channel_type}, limit: {channel_limit}) added successfully! {request.remote_addr}')
        return True
    else:
        return False
    
@app.route('/add', methods=['GET', 'POST'])
def add_channel():
    remote_addr = request.remote_addr
    #print(f'ip return as {remote_addr}')
    if remote_addr == '127.0.0.1' or remote_addr.startswith('10.0.0.'):
        if request.method == 'POST':        
            channel_id = request.form['channel_id']
            channel_type = request.form['channel_type']
            channel_limit = request.form['channel_limit']
        #channel_filter = request.form['channel_filter', 'none']

            if process_form(channel_id, channel_type, channel_limit):
                return redirect('/add')  # Redirect to clear form after success

        return render_template('add_channel.html')
  
if __name__ == '__main__':
      app.add_url_rule('/opml_form', view_func=opml_form)
      app.run(host='0.0.0.0', port=5895)
     
