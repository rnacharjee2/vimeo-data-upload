import requests

filename = "567502335"

base_url = f"https://livestreamingstorage1.blob.core.windows.net/videos/{filename}/hls/"

ff = f"https://livestreamingstorage1.blob.core.windows.net/videos/{filename}/hls/{filename}.m3u8"

# Download the M3U8 file using requests
response = requests.get(ff)
if response.status_code == 200:
    m3u8_content = response.content

    # Save the content to a local file
    with open(f"{filename}.m3u8", "wb") as file:
        file.write(m3u8_content)

    # Read the local file and modify it
    with open(f"{filename}.m3u8", "r") as file:
        lines = file.readlines()

    with open(f"{filename}.m3u8", "w") as file:
        for line in lines:
            if line.endswith(".ts\n"):
                linkSplit = line.split("/")
                line = linkSplit[-1]
                file.write(base_url + line)
            else:
                file.write(line)
else:
    print("Failed to retrieve the M3U8 file.")
