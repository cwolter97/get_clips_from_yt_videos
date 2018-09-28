#!/usr/bin/env python3

"""
Script used to download videos from youtube video, then crop random chunks based on values in config.json
"""

import json
import random
import os
from time import sleep, time
from pytube import YouTube
from pytube.exceptions import VideoUnavailable
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

def extract_chunk(video_path,start,end,targetname):
	m = int(start/60)
	mr = start%60
	s = int(end/60)
	sr = end%60
	# Shows timestamp of chunk being extracted
	print("Extracting {:02d}:{:02d} - {:02d}:{:02d} from {}".format(m,mr,s,sr,video_path.split('/')[-1]))
	path = settings['output_directory']
	ffmpeg_extract_subclip(video_path, start, end, targetname=path+targetname)

def get_chunks(stream,file_handle):
	chunk_quantity = settings['chunk_quantity']
	chunk_seconds = settings['chunk_seconds']
	ignore_start_seconds = settings['ignore_start_seconds']
	ignore_end_seconds = settings['ignore_end_seconds']

	# gets name from open file handle (everything after the '/' and before the last '.' in full filepath)
	name = ''.join(file_handle.name.split('/')[-1].split('.')[:-1])

	for i in range(chunk_quantity):
		print("\n\nGetting Chunk {}".format(i+1))
								# bounds the max int so we won't ever get a clip that goes into our ignored setting
		start_rand = random.randint(ignore_start_seconds,(int(stream.length)-(ignore_end_seconds+chunk_seconds)))
		end_rand = start_rand + chunk_seconds

		extract_chunk(file_handle.name,start_rand,end_rand,name+" - CHUNK {}.mp4".format(i+1))

	# Cleanup, remove original file
	os.remove(file_handle.name)

def download_video(video_url,quality,download_path):
	# TODO:
	# Complete quality_order list.
	# Make hybrid that will download higher quality video then combine audio to accomplish higher quality chunks. 

	quality_order = ['144p', '240p', '360p', '480p', '720p', '1080p']

	quality_index = quality_order.index(quality)

	yt_obj = YouTube(video_url, on_complete_callback=get_chunks)

	yt = yt_obj.streams.filter(file_extension='mp4').all()
	
	# Decide which to download
	found_quality = False
	while not found_quality and quality_index >= 0:
		for v in yt:
			if quality == v.resolution and v.includes_audio_track:
				found_quality = True
				yt = v
				break
		if not found_quality:
			# Decrement to next quality in list
			old_quality = quality
			quality_index -= 1		
			quality = quality_order[quality_index]
			print("Video + Audio not available in {}. Looking in {} now.".format(old_quality,quality))

	if not found_quality:
		raise VideoUnavailable

	print("Downloading {}".format(yt_obj.title))
	yt.__setattr__('length',yt_obj.length)
	yt.download(download_path)

	return yt_obj

def main():
	# TODO:
	# Add threading to speed up when downloading multiple videos
	# Add validation on config

	video_list = settings['videos']
	quantity = settings['quantity']
	frequency = settings['frequency'] * 60 # in minutes
	output_directory = settings['output_directory']
	quality = settings['quality']

	# Create target Directory if don't exist
	if not os.path.exists(output_directory):
	    os.mkdir(output_directory)

	# Loop through video list, pausing between downloads
	for index in range(0,len(video_list),quantity):
		random.seed(time())
		for video_url in video_list[index:index+quantity]:
			try:
				video = download_video(video_url,quality,output_directory)
			except VideoUnavailable:
				print("\nVideo is unavailable - {}".format(video_url))
			
		# After done with the video
		print("\nSleeping for {} minutes...".format(frequency/60))
		sleep(frequency)

#Load settings
with open('config.json') as config_file:
	settings = json.load(config_file)

if 'videos' not in settings:
	with open('videos.txt') as video_file:
		settings['videos'] = video_file.readlines()

if __name__ == "__main__":
	# TODO: Allow command-line arguments to set config file and/or video list file
	main()

__author__ = "Cody Wolter"
__copyright__ = "Copyright 2018"
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Cody Wolter"
__email__ = "cwolter97@gmail.com"
__status__ = "Prototype"
