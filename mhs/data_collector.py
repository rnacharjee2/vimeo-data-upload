import requests
import csv
import time

video_csv_file = "mhs_video.csv"
header_name = "videoid"
video_id_list = []

with open(video_csv_file, mode='r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        video_id = row.get(header_name, "")
        video_id_list.append(video_id)


# List of URLs to fetch JSON data from

main_url = "https://api.vimeo.com/me/videos/"


# Define your authorization token
authorization_token = "Bearer d83d332f82236a5fdafc80b598310b6f"

# Define the CSV file and column headers
output_csv_file = "mhs_output.csv"
# Adjust column headers as needed
csv_headers = ["video_id", "quality", "rendition", "type", "width",
               "height", "public_name", "fps", "size", "size_short", "link"]

# Initialize an empty list to store the data
data_to_write = []

# Iterate through the URLs
for counter, id in enumerate(video_id_list):
    url = f'https://api.vimeo.com/me/videos/{id}'
    print(counter)
    try:
        headers = {"Authorization": authorization_token}
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check for HTTP errors

        json_data = response.json()  # Parse JSON response
        print()
        files_data = json_data['files']
        for x in files_data:

            # Extract the information you want from the JSON response
            video_id = id
            quality = x.get("quality", "")
            rendition = x.get("rendition", "")
            type = x.get("type", "")
            width = x.get("width", "")
            height = x.get("height", "")
            public_name = x.get("public_name", "")
            fps = x.get("fps", "")
            size = x.get("size", "")
            size_short = x.get("size_short", "")
            link = x.get("link", "")

            # Append the data to the list
            data_to_write.append([video_id, quality, rendition, type, width,
                                 height, public_name, fps, size, size_short, link])

    except Exception as e:
        print(f"Error fetching data from {url}: {e}")

# Write the data to a CSV file
with open(output_csv_file, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(csv_headers)
    writer.writerows(data_to_write)

print(f"Data saved to {output_csv_file}")
