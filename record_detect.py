import cv2
import os
from openai import OpenAI
import base64
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
from pdf2image import convert_from_path
from PIL import Image



def capture(frame):
     cv2.imwrite("frame.jpg", frame)
     return


def get_album_name():
    # Function to encode the image
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
        
    image_path="frame.jpg"


    # Getting the base64 string
    base64_image = encode_image(image_path)

    response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
        "role": "system",
        "content": [
            {
            "type": "text",
            "text": " I want you to act as a Album Cover Detector. When receiving an image search the image for only album covers and return the proper album title and artist to the user. Use the following return type: {\"Album Name\": \"\", \"Artist\": \"\"}."
            },
        ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What album cover in this image?",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ],
        }
    ],
    response_format={
        "type": "text"
    },
    temperature=1,
    max_completion_tokens=2048,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )
    print(response.choices[0].message.content)

    # Parse the JSON string into a Python dictionary
    response_data = json.loads(response.choices[0].message.content)

    # Extract variables from the parsed JSON
    album_name = response_data["Album Name"]
    artist = response_data["Artist"]

    # Print the extracted values
    print(f"Album Name: {album_name}")
    print(f"Artist: {artist}")

    return album_name,artist

def get_album_data(album_name,artist):

    # Authenticate Spotipy
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
        redirect_uri="http://192.168.2.90:8000/callback",
        scope="user-read-private,playlist-modify-public,playlist-modify-private"  # Use 'playlist-modify-private' for private playlists
    ))

    query = f"album:{album_name} artist:{artist}"
    results = sp.search(q=query, type="album", limit=1)

    if results['albums']['items']:
        album = results['albums']['items'][0]
        album_id = album['id']
        
        # Get the album's tracks
        tracks = sp.album_tracks(album_id)
        
        # Extract track names
        tracklist = [track['name'] for track in tracks['items']]
        
        return tracklist
    else:
        return f"No album found for '{album_name}' by {artist}."

def convert_to_projector(album_name, artist_name, tracklist, output_path="album_tracklist.pdf"):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    # Create a PDF canvas
    c = canvas.Canvas(output_path, pagesize=letter)

    # Set up title and header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, f"Album: {album_name}")
    c.setFont("Helvetica", 12)
    c.drawString(100, 730, f"Artist: {artist_name}")
    
    # Set up the tracklist section
    c.setFont("Helvetica", 10)
    y_position = 700  # Starting Y position for the tracklist

    # Add each track to the PDF
    for i, track in enumerate(tracklist, 1):
        if y_position < 100:  # Check if we need to add a new page
            c.showPage()  # Add a new page
            c.setFont("Helvetica", 10)
            y_position = 750  # Reset Y position for new page
        c.drawString(100, y_position, f"{i}. {track}")
        y_position -= 15  # Move down the Y position for the next track
    
    # Save the PDF
    c.save()


def convert_to_png(pdf_path,png_path):
    images = convert_from_path(pdf_path)

    for i in range(len(images)):
  
      # Save pages as images in the pdf
        images[i].save('page'+ str(i) +'.png', 'PNG')


# Authenticate OPENAI
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),  
)

if __name__=="__main__":

    # Create a VideoCapture object
    cap = cv2.VideoCapture(0)  # 0 represents the default camera

    # Check if the camera is opened successfully
    if not cap.isOpened():
        print("Error opening video stream or file")

    while True:
        # Read a frame from the camera
        ret, frame = cap.read()

        # If frame is read correctly, ret is True
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break

        # # Display the frame
        # cv2.imshow('Webcam', frame)

        capture(frame)
        break
  

    # Release the VideoCapture object
    cap.release()
    cv2.destroyAllWindows()
    print("picture taken")

    album_name,artist=get_album_name()
    tracklist = get_album_data(album_name,artist)
    for track in tracklist:
        print(track)
    convert_to_projector(album_name=album_name,artist_name=artist,tracklist=tracklist)
    convert_to_png("album_tracklist.pdf","page0.png")
    






