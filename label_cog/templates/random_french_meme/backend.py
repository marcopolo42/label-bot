import requests


def fetch_meme():
    api_endpoint = "https://meme-api.com/gimme/FrenchMemes"

    try:
        # Make a GET request to the API
        response = requests.get(api_endpoint)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

        # Parse the response as JSON
        data = response.json()

        # Extract the image URL
        print("Data:")
        print(data)
        print("Data end")
        meme_url = data.get('url', None)
        if not meme_url:
            raise ValueError("No 'url' field in the API response.")

        # Return the meme URL to be used in the template
        return {"success": True, "url": meme_url, "message": "Meme fetched successfully!"}

    except requests.exceptions.RequestException as e:
        # Handle request errors
        return {"success": False, "url": None, "message": f"Failed to fetch meme: {e}"}
    except ValueError as e:
        # Handle missing or malformed data errors
        return {"success": False, "url": None, "message": str(e)}


# Example usage:
async def process_data(data):
    result = fetch_meme()
    if result["success"]:
        data = {"meme_url": result["url"]}
        print("Meme fetched successfully!")
        print(f"Meme URL: {result['url']}")
        print("Data out:")
        print(data)
        print("Data out end")
        return data
    else:
        print(result["message"])
        return None
