import requests
import csv
import os


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


for x in video_link_list[0:2]:
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
