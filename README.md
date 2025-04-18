# Minecraft Server Creator

A simple GUI application to help you create Minecraft servers.

## Features
- Select server type (Paper, Vanilla, Spigot)
- Select any Minecraft version
- Configure RAM allocation and CPU cores
- Multi-threaded download
- Automatic server file download
- Creates optimized startup script
- Automatically accepts EULA

## Requirements
- Python 3.7 or higher
- Required packages (install using `pip install -r requirements.txt`):
  - requests
  - PyQt5

## How to Use
1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
2. Run the program:
   ```
   python server_creator.py
   ```
3. Select your desired server type (Paper, Vanilla, or Spigot)
4. Select your desired Minecraft version
5. Click "Create Server"
6. In the settings window:
   - Choose RAM allocation (1-32 GB)
   - Select number of CPU cores to use
7. Click "Create Server" in the settings window
8. The server files will be created in a `server` folder

## Server Files
After creation, you'll find these files in the `server` folder:
- `server.jar` - The server file
- `start.bat` - Optimized startup script with your settings
- `eula.txt` - EULA agreement file

## Starting the Server
1. Navigate to the `server` folder
2. Double-click `start.bat`
3. The server will start and generate the world

## Notes
- Make sure you have Java installed on your system
- The first startup might take longer as it generates the world
- Default port is 25565 (can be changed in server.properties)
- The startup script is optimized with G1GC garbage collector and parallel threads 