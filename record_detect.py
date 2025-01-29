import cv2
import os
from openai import OpenAI
import base64
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import pygame
import requests

# Initialize Pygame
pygame.init()

# Fonts
FONT_TITLE = pygame.font.SysFont("Arial", 40)
FONT_TEXT = pygame.font.SysFont("Arial", 24)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (176,0,5)
LIGHT_RED=(255,128,128)

# Screen Dimensions
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600

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

def download_album_cover(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Album cover saved to {save_path}")
    else:
        print("Failed to download the album cover.")


def get_album_data(album_name,artist):

    # Authenticate Spotipy
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
        redirect_uri="http://localhost:8000/callback",
        scope="user-read-private,playlist-modify-public,playlist-modify-private",  # Use 'playlist-modify-private' for private playlists
        open_browser=False 
    ))



    query = f"album:{album_name} artist:{artist}"
    results = sp.search(q=query, type="album", limit=1)

    if results['albums']['items']:
        album = results['albums']['items'][0]
        album_id = album['id']
        cover_url = album["images"][0]["url"]  # 640px by 640px
        # Get the album's tracks
        tracks = sp.album_tracks(album_id)
        
        # Extract track names
        tracklist = [track['name'] for track in tracks['items']]

        # Get the album cover URL (choose size: 640px, 300px, or 64px)
        cover_url = album["images"][0]["url"]  # 640px by 640px
        download_album_cover(cover_url,"album_cover.jpeg")
        return tracklist
    else:
        return f"No album found for '{album_name}' by {artist}."
    
    


def build_album_screen(album_cover, album_name, artist_name,tracklist):
    #dimensions of pi screen
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Album Display")

    # Load the image
    image = pygame.image.load(album_cover)
    image = pygame.transform.scale(image, (300, 300))  # Resize if needed

    # Scrolling parameters
    visible_items = 8  # Number of tracklist items visible at once
    scroll_position = 0  # Tracks the current scroll position

    running = True
    while running:
        # Fill the screen with black
        screen.fill(BLACK)

        # Display the image
        screen.blit(image, (50, 150))  # Position the image (x=50, y=50)

        # Display text
        now_playing = FONT_TITLE.render(f"Now Playing: ", True, RED)
        screen.blit(now_playing, (500, 50))
        title_surface = FONT_TITLE.render(f"Album: {album_name}", True, WHITE)
        artist_surface = FONT_TITLE.render(f"Artist: {artist_name}", True, WHITE)
        screen.blit(title_surface, (500, 120))  # Position text to the right of the image
        screen.blit(artist_surface, (500, 170))

        # Display a subset of the tracklist based on scroll_position
        y_offset = 240
        for i in range(scroll_position, min(scroll_position + visible_items, len(tracklist))):
            track_surface = FONT_TEXT.render(f"{i + 1}. {tracklist[i]}", True, WHITE)
            screen.blit(track_surface, (500, y_offset))
            y_offset += 30

        # Draw buttons
        up_button = pygame.Rect(400, 300, 50, 50)  # (x, y, width, height)
        down_button = pygame.Rect(400, 400, 50, 50)
        exit_button = pygame.Rect(50, 50, 50, 50)
        pygame.draw.rect(screen, WHITE, up_button)
        pygame.draw.rect(screen, WHITE, down_button)
        pygame.draw.rect(screen, WHITE, exit_button)


        # Button labels
        up_text = FONT_TEXT.render("↑", True, BLACK)
        down_text = FONT_TEXT.render("↓", True, BLACK)
        exit_text = FONT_TEXT.render("X", True, BLACK)
        screen.blit(up_text, (420, 310))
        screen.blit(down_text, (420, 410))
        screen.blit(exit_text, (65, 60))


        pygame.display.flip()

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if up_button.collidepoint(event.pos) and scroll_position > 0:
                    scroll_position -= 1  # Scroll up
                elif down_button.collidepoint(event.pos) and scroll_position + visible_items < len(tracklist):
                    scroll_position += 1  # Scroll down
                elif exit_button.collidepoint(event.pos):
                    build_start_screen()



    pygame.quit()


def build_start_screen():
    # Screen dimensions
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Album Detector")

    # Button properties
    detect_button = pygame.Rect(SCREEN_HEIGHT/2, 150, 400, 100)  # (x, y, width, height)

    quit_button=pygame.Rect(SCREEN_HEIGHT/2, 350, 400, 100)

    def run_detection():

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

        build_album_screen(album_cover="album_cover.jpeg",album_name=album_name,artist_name=artist,tracklist=tracklist)

    running = True
    while running:
        screen.fill(BLACK)

        # Get mouse position
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        # Change detect button color on hover
        if detect_button.collidepoint(mouse_pos):
            pygame.draw.rect(screen, RED, detect_button)
            if mouse_pressed[0]:  # Left mouse button clicked
                run_detection()
        else:
            pygame.draw.rect(screen, LIGHT_RED, detect_button)

        # Change quit button color on hover
        if quit_button.collidepoint(mouse_pos):
            pygame.draw.rect(screen, RED, quit_button)
            if mouse_pressed[0]:  # Left mouse button clicked
                running=False
        else:
            pygame.draw.rect(screen, LIGHT_RED, quit_button)

        # Render button text
        detect_text = FONT_TITLE.render("Detect Album", True, WHITE)
        detect_text_rect = detect_text.get_rect(center=detect_button.center)
        screen.blit(detect_text, detect_text_rect)

        quit_text = FONT_TITLE.render("Quit", True, WHITE)
        quit_text_rect = quit_text.get_rect(center=quit_button.center)
        screen.blit(quit_text, quit_text_rect)

        # Event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update display
        pygame.display.flip()

    # Quit Pygame
    pygame.quit()


if __name__=="__main__":

    # Authenticate OPENAI
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),  
    )

    build_start_screen()
    





