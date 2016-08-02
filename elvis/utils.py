import os

def create_directories(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)