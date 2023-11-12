import requests
import csv
import os
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import subprocess
import shutil

video_link_csv = 'output.csv'

video_link_list = []
success_log_file = 'success_log.txt'
# Load the list of successfully downloaded video URLs from the log file
downloaded_urls = set()

if os.path.exists(success_log_file):
    with open(success_log_file, 'r') as log_file:
        downloaded_urls.update(line.strip() for line in log_file)


with open(video_link_csv, mode='r') as file:
    reader = csv.DictReader(file)
    for row in reader:

        video_link_list.append(dict(row))

for x in video_link_list[0:10]:
    video_id = x['video_id']
    video_url = x['link']
    rendition = x['rendition']

    if rendition == "adaptive":
        print("hls file skipped")
        continue

    # Check if the video URL has already been successfully downloaded
    if video_url in downloaded_urls:
        print(f"Video at URL already downloaded. Skipping.")
        continue

    # creating parent folder
    parent_folder = video_id
    if not os.path.exists(parent_folder):
        os.makedirs(parent_folder)

    file_name = f'{video_id}_{rendition}.mp4'

    file_path = os.path.join(parent_folder, file_name)

    response = requests.get(video_url)
    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"Video downloaded and saved at: {file_path}")
        # Log the successful download in the log file
        with open(success_log_file, 'a') as log_file:
            log_file.write(video_url + '\n')
    else:
        print(
            f"Failed to download the video. Status code: {response.status_code}")
        


    account_name = 'livestreamingstorage1'
    account_key = 'ERarnb2Bu9RV7D5vwZYUwX23OWftF5PPrSHFbGueXF74QBpIKNt5nBhjMu3yV2ZUwgOBE/ib7nOs+AStsG7SzQ=='
    container_name = 'videos'
    local_file_path = os.path.join(parent_folder, file_name)
    blob_name = f'{video_id}/{video_id}_{rendition}.mp4' # The name for the blob in Azure Blob Storage

    # Create a connection to the Blob Service
    blob_service_client = BlobServiceClient(account_url=f"https://{account_name}.blob.core.windows.net", credential=account_key)

    # Create a container client (or use an existing one)
    container_client = blob_service_client.get_container_client(container_name)

    # Create a blob client
    blob_client = container_client.get_blob_client(blob_name)

    # Upload the video file to Azure Blob Storage
    try:
        with open(local_file_path, "rb") as data:
            blob_client.upload_blob(data)

        print(f"Uploaded {local_file_path} to {container_name}/{blob_name}")
    except:
        print(f"Failed to upload {local_file_path} to {container_name}/{blob_name}")

    #create a m3u8 file using ffmpeg

    
    # creating hls folder
    hls_folder = os.path.join(parent_folder, 'hls')
    if not os.path.exists(hls_folder):
        os.makedirs(hls_folder, exist_ok=True)
    

    input_file = f'{video_id}/{video_id}_540p.mp4'
    output_directory = hls_folder
    output_file = f'{video_id}.m3u8'
    output_path = os.path.join(output_directory, output_file)

    # file_name_end =os.path.join(output_directory, f'{video_id}_%03d.ts')


    if os.path.exists(input_file):
        ffmpeg_command = [
            'ffmpeg',
            '-i', input_file,
            '-c:v', 'h264',
            '-c:a', 'aac',
            '-f', 'hls',
            '-hls_time', '10',
            '-hls_list_size', '0',
            '-hls_segment_filename', os.path.join(output_directory, f'{video_id}_%03d.ts') ,
            output_path
        ]

        # run ffmpeg as subprocess
        try:
            subprocess.run(ffmpeg_command, check=True)
            # print(f"Successfully created HLS playlist at {output_path}")
            m3u8_file_path = os.path.join(parent_folder, 'hls', f'{video_id}.m3u8')
            with open(m3u8_file_path, "w") as m3u8_file:
                m3u8_file.write("#EXTM3U\n")
                m3u8_file.write(f"#EXT-X-VERSION:3\n")
                m3u8_file.write(f"#EXT-X-TARGETDURATION:17\n")

            number_of_segments = len(os.listdir(hls_folder))
            print(number_of_segments)

                # for i in range(1, number_of_segments +1)


        except subprocess.CalledProcessError as err:
            print(f"Error executing ffmpeg command: {err.stderr}")
    else:
        print(f"Input file {input_file} does not exist")
       
    # now i want to create a blob for each ts file inside the hls folder

    # get the list of ts files
    ts_files = os.listdir(hls_folder)
    ts_files = [os.path.join(hls_folder, file) for file in ts_files ]
   


    # upload each ts file to azure blob storage
    hls_file_path = os.path.join(parent_folder, 'hls')
    for file in ts_files:
        
        # get the file name
        file_name = os.path.basename(file)
        # create the blob name
        blob_name = f'{video_id}/hls/{file_name}'
        # create the blob client
        blob_client = container_client.get_blob_client(blob_name)
        # upload the file
        try:
            with open(file, "rb") as data:
                blob_client.upload_blob(data)
            print(f"Uploaded {file} to {container_name}/{blob_name}")
        except:
            print(f"Failed to upload {file} to {container_name}/{blob_name}")

    # delete the local files


    # try:
    #     shutil.rmtree(parent_folder)
    #     print(f"Successfully removed the directory: {parent_folder}")
    # except Exception as e:
    #     print(f"Error removing the directory: {e}")



    