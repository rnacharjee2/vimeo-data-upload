import requests
import csv
import os
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import subprocess
import shutil
import time

video_link_csv = 'mhs_output.csv'

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

total_url_without_hls = 0
for x in video_link_list:
    if x['rendition'] != "adaptive":
        total_url_without_hls += 1


video_id_check_folder_removal = None

for x in video_link_list[1900:3852]:
    
    video_id = x['video_id']
    video_url = x['link']
    rendition = x['rendition'] 

    if rendition == "adaptive":
        print("hls file skipped")
        continue

    # Check if the video URL has already been successfully downloaded
    if video_url in downloaded_urls:
        print(f"Video at URL already downloaded and uploaded . >>> Skipping.")
        continue

    # creating parent folder
    parent_folder = video_id
    if not os.path.exists(parent_folder):
        os.makedirs(parent_folder)

    file_name = f'{video_id}_{rendition}.mp4'

    file_path = os.path.join(parent_folder, file_name)

    # check if the video file already exists in the local folder
    if os.path.exists(file_path):
        print(f"Video already exists. Skipping download.")
    else:
        print(f"Video Downloading Started ........")
        response = requests.get(video_url)
        if response.status_code == 200:
            with open(file_path, 'wb') as file:
                file.write(response.content)
            print(f"Video downloaded and saved at: {file_path}")
            # Log the successful download in the log file
            
        else:
            print(f"Failed to download the video. Status code: {response.status_code}")
            continue
            


    account_name = 'ctallstorage'
    account_key = '6G6P/YPwFD7x9xSLj5agJ3yT2zRLBFmhOfeWxH7WoD2Mh3Dia4CmrEYD7+zwJTJHkFPrVpu439kc+ASt4KRcAQ=='
    container_name = 'videos'
    local_file_path = os.path.join(parent_folder, file_name)
    blob_name = f'{video_id}/{video_id}_{rendition}.mp4' # The name for the blob in Azure Blob Storage

    # Create a connection to the Blob Service
    blob_service_client = BlobServiceClient(account_url=f"https://{account_name}.blob.core.windows.net", credential=account_key)

    # Create a container client (or use an existing one)
    container_client = blob_service_client.get_container_client(container_name)

    # Create a blob client
    blob_client = container_client.get_blob_client(blob_name)

    # check if the blob exists

    if blob_client.exists():
        print(f"Blob {blob_name} already exists. Skipping.")
    else:
        #Upload the video file to Azure Blob Storage
        try:
            with open(local_file_path, "rb") as data:
                blob_client.upload_blob(data)

            print(f"Uploaded {local_file_path} to {container_name}/{blob_name}")
        except:
            print(f"Failed to upload {local_file_path} to {container_name}/{blob_name}")

            # create a failed log if failed to upload
            with open('failed_blob_upload_log.txt', 'a') as log_file:
                log_file.write(video_url + '\n')
            continue
                


    #create a m3u8 file using ffmpeg
    # creating hls folder
    hls_folder = os.path.join(parent_folder, 'hls')
    if not os.path.exists(hls_folder):
        os.makedirs(hls_folder, exist_ok=True)
    

    # file_name_end =os.path.join(output_directory, f'{video_id}_%03d.ts')

    # check if the m3u8 file already exists and also check the video_id rendition is 540p
    # if it is not 540p then skip
    # else run ffmpeg command

    if x["rendition"] != "540p":
        print(f" >>>>> it is not 540p. SKIPPING m3u8 generation.")

    else:
        try:
            input_file = f'{video_id}/{video_id}_540p.mp4'
            output_directory = hls_folder
            output_file = f'{video_id}.m3u8'
            output_path = os.path.join(output_directory, output_file)
            print("Entered in hls file creation")
            
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
                
                subprocess.run(ffmpeg_command, check=True)
                
            else:
                print(f"Input file {input_file} does not exist")
        except:
            print(f"Error executing ffmpeg command: ")
            continue
        
        # now i want to create a blob for each ts file inside the hls folder

        # get the list of ts files
        ts_files = os.listdir(hls_folder)
        ts_files = [os.path.join(hls_folder, file) for file in ts_files ]
    
        # upload each ts file to azure blob storage

        try: 
            hls_file_path = os.path.join(parent_folder, 'hls')
            for file in ts_files:
                
                # get the file name
                file_name = os.path.basename(file)
                # create the blob name
                blob_name = f'{video_id}/hls/{file_name}'
                # create the blob client
                blob_client = container_client.get_blob_client(blob_name)
                # upload the file
                # check if the blob exists
                if blob_client.exists():
                    print(f"Blob {blob_name} already exists. Skipping.")
                    
                else:
                    try:
                        with open(file, "rb") as data:
                            blob_client.upload_blob(data)
                        print(f"Uploaded {file} to {container_name}/{blob_name}")
                    except:
                        print(f"Failed to upload {file} to {container_name}/{blob_name}")
            
                        # create a failed log if failed to upload
                        with open('failed_ts_upload_log.txt', 'a') as log_file:
                            log_file.write(video_url + '\n')
        except:
            print(f"Failed to upload {file} to {container_name}/{blob_name}")
            
            # create a failed log if failed to upload
            with open('failed_ts_upload_log.txt', 'a') as log_file:
                log_file.write(video_url + '\n')
            continue
                        

                
    # # delete the local files

    # Check if video is downloading to a new folder
    if video_id_check_folder_removal == None:
        video_id_check_folder_removal = video_id
        print(f"Video ID check folder removal set to: {video_id_check_folder_removal}")
    elif video_id_check_folder_removal != video_id:
        try:
            # check if the m3u8 file exists in the delete folder, if not write to hls_failed log file
            m3u8_file_path = os.path.join(video_id_check_folder_removal, 'hls', f'{video_id}.m3u8')

            if not os.path.exists(m3u8_file_path):
                with open('hls_failed_log.txt', 'a') as log_file:
                    log_file.write(video_url + '\n')

            shutil.rmtree(video_id_check_folder_removal)
            print(f"Successfully removed the directory: {video_id_check_folder_removal}")
        except Exception as e:
            print(f"Error removing the directory: {e}")
        video_id_check_folder_removal = video_id
        print(f"Video ID check folder removal set to: {video_id_check_folder_removal}")
    else:
        print(f"Still in Same Folder: {video_id_check_folder_removal}")
    
    # write to success log file
    with open(success_log_file, 'a') as log_file:
        log_file.write(video_url + '\n')
    
    # Check if the m3u8 file exists. if not exists then write to hls_failed log file


    # Count the url in success_log_file
    total_success = 0


    # get total success downloaded 

    with open(success_log_file, 'r') as log_file:
        for line in log_file:
            total_success += 1

    
    
    percentage = round(total_success / total_url_without_hls * 100, 2)  
    print(f'----------------------------------------  PROGRESS >>>>> {total_success} / {total_url_without_hls} completed,  percentage = {percentage} % -------------')



    