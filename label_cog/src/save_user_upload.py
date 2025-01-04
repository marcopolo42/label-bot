import os.path

import requests


async def save_file_uploaded(message, folder):
    print(f"Message: {message}")
    try:
        url = message.attachments[0].url
        name = message.attachments[0].filename
    except IndexError:
        print("Error: No attachments")
        await message.channel.send("No attachments found in your message")
    else:
        if url.startswith("https://cdn.discordapp.com"):
            r = requests.get(url, stream=True) # enable streaming in chunks
            print(f"file name: {name}")
            with open(os.path.join(folder, name), 'wb') as out_file:
                print('Saving image: ' + folder + "/" + name)
                for chunk in r.iter_content(chunk_size=8192): # write in chunks for better memory usage
                    out_file.write(chunk)
            print('Image saved')
            await message.channel.send("Image saved successfully")
        else:
            print("Error: Invalid URL")
