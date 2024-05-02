from flask import Flask, request, send_from_directory, render_template, redirect, flash, Response
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
XML_DIRECTORY = os.path.join(os.getcwd(), 'xml_files')
CAST_DOMAIN = os.getenv('CAST_DOMAIN')
CAST_TRUSTED_NETWORK = os.getenv('CAST_TRUSTED_NETWORK','127.0.0.1').split(',')
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
@app.route('/manage')
def index():
    remote_addr = request.remote_addr
    if any(remote_addr.startswith(pattern) for pattern in CAST_TRUSTED_NETWORK):
        cleanit()
        with open(file_path, 'r') as file:
            lines = file.readlines()  # Read all lines from the file
        return render_template('manage.html', lines=lines)
    else:
        return redirect('/')

@app.route('/add_line', methods=['POST'])
def add_line():
    remote_addr = request.remote_addr
    if any(remote_addr.startswith(pattern) for pattern in CAST_TRUSTED_NETWORK):
        new_line = request.form.get('new_line')  # Get the new line from the form
        # Check if the file is empty
        file_empty = os.stat(file_path).st_size == 0

        with open(file_path, 'a') as file:
            if not file_empty:  # If the file is not empty, add a newline character before the new line
                file.write('\n')
            file.write(new_line)  # Append the new line to the file 
            cleanit()
    return redirect('/manage')
def cleanit():
    line_to_remove = ''  # Get the line to remove from the form
    with open(file_path, 'r') as file:
        lines = file.readlines()  # Read all lines from the file
    with open(file_path, 'w') as file:
        for line in lines:
            if line.strip() != line_to_remove.strip() and line.strip() != '':  # Remove if not an empty line or just spaces
                file.write(line)



@app.route('/remove_line', methods=['POST'])
def remove_line():
    remote_addr = request.remote_addr
    if any(remote_addr.startswith(pattern) for pattern in CAST_TRUSTED_NETWORK):
        new_line = request.form.get('new_line')  # Get the new line from the form
        line_to_remove = request.form.get('line_to_remove')  # Get the line to remove from the form
        print(line_to_remove)
        with open(file_path, 'r') as file:
            lines = file.readlines()  # Read all lines from the file
        with open(file_path, 'w') as file:
            for line in lines:
                if line.strip() != line_to_remove.strip():  # Write all lines except the one to remove
                    file.write(line)
        cleanit()
    return redirect('/manage')        

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
 links_html = '<a href="/opml">OPML</a> | <a href="/manage">Manage</a><br>'
 return f'{logo_html}{links_html}<h1>XML Files:</h1>{file_links}'

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
  if domain:
    files = [f for f in os.listdir(XML_DIRECTORY) if f.endswith('.xml')]
    opml_data = generate_opml(files, domain)
    return Response(opml_data, mimetype='text/xml')
  else:
    # Redirect to form if no domain submitted
    return redirect('/')

  files = [f for f in os.listdir(XML_DIRECTORY) if f.endswith('.xml')]
  opml_data = generate_opml(files, domain)
  return Response(opml_data, mimetype='text/xml')
  
if __name__ == '__main__':
      app.run(host='0.0.0.0', port=5895)
     
