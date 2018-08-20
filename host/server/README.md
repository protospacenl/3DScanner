# Install prerequisites

* Install [python3](https://www.python.org/ftp/python/3.6.6/python-3.6.6-amd64.exe)
* Install [opencv3](https://sourceforge.net/projects/opencvlibrary/files/opencv-win/3.4.2/opencv-3.4.2-vc14_vc15.exe/download)

(OpenCV is only used for image colorspace conversion. Needs to be removed: #1).


# Install python dependencies

    cd host\server
    pip3 install -r requirements.txt

# Run program

    cd host\server
    python server.py
Or doubleclick `server.py` 