# This script defines functions for file management

import os
import json
import csv
from ij import IJ
import io
import copy
from java.io import File

class Config:
    # This class will convert the json format of the config into an object

    def __init__ (self,config,path):
        # Input the config dictionary
        self.original = config # Save the original file structure
        self.roi_set = config["Set ROI Image"] # Define image to base rois on
        self.roi_measure = config["Measure ROI Image"] # Define images to measure with rois
        self.roi_name = config["ROI Names"] # Define the names of the rois
        self.next_image = config['Open Next Image'] # Define whether or not the user wants to open the next image
        self.path = path # Pull the listed file path

def load_config(plugin_path):
    # Function that loads the config.py file
    with io.open(os.path.join(plugin_path, "config.json"),'r',encoding='utf-8') as file: # Open the config json file
        json_config = json.load(file) # Load the config file
    try:
        with io.open(os.path.join(plugin_path,"filePath.txt"),'r',encoding='utf-8') as file: # Open the file path text file
            path = str(file.read()) # Load the file path as a string
    except:
        # If the file path file is not made
        path = '' # Initialize the path as an empty string
    return Config(json_config,path) # Return the config converted into an object

def find_in_directory(directory,identifier):
    # Funciton that searches the current directory and returns a path to the file matching the inputted string identifier
    # Where config.path is a path object of a file in the desired directory to be searched
    for file in os.listdir(directory):
        # Loop through each file in the directory, where file is the file name only
        if identifier in file:
            # Return the path of the file containing the identifier
            return os.path.join(directory,file) # Return the path to the file

def get_roi_folder(image_path):
    # Method to find the path to the ROI folder and make one if it does not exist
    master_dir = os.path.dirname(os.path.dirname(os.path.dirname(image_path))) # Master directory is three levels above the current image
    roi_path = os.path.join(master_dir,"ROIs/") # ROI directory is within the master directory
    try:
        os.makedirs(roi_path) # Make the directory
        return roi_path
    except OSError:
        # If the directory already exists
        return roi_path

def save_results(config,results):
    # Update acquired results (append excel sheet and update config)
    master_dir = os.path.dirname(os.path.dirname(os.path.dirname(config.path))) # Master directory is three levels above the current image
    IJ.log(master_dir)

    for stain in config.roi_measure:
        # Loop through each stain being measured
        csv_path = os.path.join(master_dir,stain+"_results.csv") # Define the path to the current csv

        if os.path.exists(csv_path):
            # If the csv path exists
            with io.open(csv_path, 'rb') as file:
                # Open the csv file
                data = list(csv.reader(file)) # Read the file
        else:
            # If the csv path does not exist
            data = [['Image', 'Stain','ROI']] # Initialize the first three headers of the first row

        isolated_results = copy.deepcopy(results) # Create a copy of the results to isolate a given stain (I used deepcopy to also copy the nested structures (mainly dictionaries))

        for image in results['Measurements']:
            # Loop through each measured image
            if results['Measurements'][image]['Stain'] != stain:
                # If the current image is for a different stain
                isolated_results['Measurements'].pop(image) # Remove the image from the isolated measurements

        data = generate_csv_rows(data,isolated_results) # Run function to add new rows

        with io.open(csv_path,'wb') as file:
            # Open the file (and wipe it clean) for writing
            writer = csv.writer(file) # Generate a csv writer object of the file
            IJ.log(str(data))
            writer.writerows(data) # Write the updated csv

def generate_csv_rows (data,results):
    # Method to append rows to the csv variable and change the header row if neccessary given the current csv data and results
    change_header = False # Initialize flag as false
    metrics = data[0][3:] # Isolate the listed metrics of the first row, skipping the first three columns
    IJ.log(str(metrics))
    for image in results['Measurements']:
        # Loop through each image that was analyzed
        for roi in results['Measurements'][image]['ROIs']:
            # Loop through each measured ROI
            row = [image,results['Measurements'][image]['Stain'],roi] # Record the image name, stain, and roi as the first three columns
            roi_measurements = results['Measurements'][image]['ROIs'][roi] # Create shortcut in the dictionary
            for metric in metrics:
                # Loop through each metric included in the header of the csv
                if metric in roi_measurements:
                    # If this metric was measured
                    row.append(roi_measurements[metric]) # Add the measurement to the row
                else:
                    row.append("") # Add a blank entry
            for metric in roi_measurements:
                # Loop through each metric in the roi_measurements
                if not metric in metrics:
                    # If this metric is not listed in the csv file
                    IJ.log(metric + " was added as a header since it was not in: " + str(metrics))
                    metrics.append(metric) # Add the metric to the list of metrics
                    row.append(roi_measurements[metric]) # Add the measurement to the row
                    change_header = True # Mark flag
            data.append(row) # Add the row to the list of rows
    if change_header:
        # If the header needs to be changed
        data[0][3:] = metrics # Update the header to incorporate the new metric(s)
    return data

def transition_path(config,script_dir):
    # Method that transitions the path to the next image in the image folder and updates the config and the file path text file

    current_image_dir = os.path.dirname(config.path) # Define the current image folder
    IJ.log("Default directory: " + current_image_dir)
    IJ.log("Reap directory: "+File(current_image_dir).getCanonicalPath())
    current_image_dir_name = os.path.basename(File(current_image_dir).getCanonicalPath()) # Define the name of the directory.
    # NOTE: I used File object from java.io since it was the only method I could find in Jython to get a conincal path without shortcuts, which is necessary for long paths
    master_image_dir = os.path.dirname(current_image_dir) # Folder of all images is one layer above any given image folder
    list_of_image_dirs = os.listdir(master_image_dir) # List all image folders
    try:
        current_index = list_of_image_dirs.index(current_image_dir_name) # Pull the index of the current image folder in its directory
    except:
        # If the index of the current folder can't be found
        IJ.log("The next image folder cannot be located.") # Inform the user
        return True
    
    try:
        while True:
            # Begin indefinite loop
            # If there is another entry afterward
            next_image_dir_name = list_of_image_dirs[current_index+1] # Get the name of the next directory
            next_image_dir = os.path.join(master_image_dir,next_image_dir_name) # Get the path to the next directory

            if os.path.isdir(next_image_dir):
                # If the next item in the directory is a directory
                break
    except:
        # If you loop through all of the folder's contents
        return True

    next_image_path = find_in_directory(next_image_dir,config.roi_set) # Find the next image to draw ROIs onto, inputting the directory and identifier of the image
    config.path = next_image_path # Update the config
        
    #Next, update the file path text file
    with io.open(os.path.join(script_dir,"filePath.txt"),'w',encoding='utf-8') as file: # Open the file
        file.write(next_image_path)

    # Reutrn that there is more content in the folder
    return False