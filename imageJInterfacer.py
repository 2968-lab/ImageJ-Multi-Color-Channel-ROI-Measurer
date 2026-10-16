# This file contains all of the needed functions that interface with ImageJ

from ij import IJ, WindowManager
from ij.plugin.frame import RoiManager
from ij.measure import ResultsTable
from ij.io import OpenDialog
import fileManager
import os
from java.awt import Frame

def check_open_image():
    # Function that checks whether an image is open in ImageJ and returns a condition and path if so
    try:
        image = IJ.getImage() # Get the currently opened image (this is effectively a check to see whether an image is opened)
        image_name = OpenDialog.getLastName() # Gets the name of the last image opened
        image_dir = OpenDialog.getLastDirectory() # Gets the directory of the last image opened
        image_path = image_dir + image_name # Generate the path from the directory and file name
        return [True,image_path] # Return that an image is open and its path
    except:
        # If no image is opened
        return [False, ""] # Return that no image iopen and a blank path

def open_image(path):
    # Function to open an image given a path to the image
    try:
        image = IJ.openImage(path) # Open the image
        image.show() # Display the image
        return True # The image was opened
    except:
        # If the image was not opened
        return False


def check_rois(rois):
    # Function that checks whether the correct number of ROIs are opened when compared with a list of inputted names for these rois. Returns true if number of ROIs is correct
    try:
        config_num_rois = len(rois) # Number of ROIs listed in the config
        rm = RoiManager.getInstance() # Get the current instance of the ROI manager
        rm_num_rois = rm.getCount() # Returns the number of ROIs listed in the ROI manager
        if config_num_rois == rm_num_rois:
            # If the ROIs match
            return True
        else:
            IJ.log("Number of ROIs in config and in the ROI manager do not match.")
            IJ.log("Number of ROIs in config = "+(config_num_rois))
            IJ.log("Number of ROIs in manager = " + str(rm_num_rois))
            return False
    except AttributeError:
        # If the ROI manager is not opened
        IJ.log("ROI manager is not opened.")
        return False

def run_analysis(config):
    # Function that runs the ImageJ analysis given an inputted config.
    # By this point, an image is gaurenteed to be open and the correct number of ROIs are present

    results = { # Initialize dicitonary of results
        "Image Folder" : os.path.basename(os.path.dirname(config.path)), # Save the name of the image folder
        "Measurements" : {} # Initialize empty dictionary of measurements
    } 

    roi_manager = RoiManager.getInstance() # Load the ROI manager
    results_table = ResultsTable.getResultsTable() # Generate a results table for the measurements

    for stain in config.roi_measure:
        # Loop through each modality image that needs to be measured
        measure_image_identifier = config.roi_measure[stain] # Identifier of the image to be opened
        new_path = fileManager.find_in_directory(os.path.dirname(config.path),measure_image_identifier) # Return the path of the desired image
        
        if new_path is None:
            # If an image could not be found
            IJ.log("An image could not be found in the directory: " + os.path.dirname(config.path) + " with the appropriate identifier: " + measure_image_identifier) # Inform the user
            return None

        image_name = os.path.basename(new_path) # Get the name of the file

        try:
            image = IJ.openImage(new_path) # Open the image
            image.show() # Show the current image so that IJ operations will be performed on it
        except:
            # If the image could not be opened
            IJ.log(image_name+" could not be opened.")
            return

        IJ.run(image,"8-bit","") # Convert the image to 8-bit

        results['Measurements'][image_name] = { # Initialize dictionary for the current image
            'Stain' : stain, # Record the stain for the image
            'ROIs' : {} # Initialize empty dictionary for the ROI measurements
        }
        
        for i,roi_name in enumerate(config.roi_name):
            # Loop through each ROI to be measured
            results_table.reset() # Reset the results table
            roi = roi_manager.getRoi(i) # Load the current number ROI from the manager
            image.setRoi(roi) # Sets the current ROI onto the image
            IJ.run("Measure") # Measure the current roi on the current image
            results['Measurements'][image_name]['ROIs'][roi_name] = {} # Create an empty dictionary for the current roi of the current image
            roi_shortcut = results['Measurements'][image_name]['ROIs'][roi_name] # Create a shortcut
    
            for heading in results_table.getHeadings():
                # Loop through each heading in the results table
                roi_shortcut[heading] = results_table.getValue(heading,0) # Extract the current value from the current heading and the first row

    results_window = WindowManager.getWindow("Results") # Load the results window
    results_window.setVisible(False)  # Hide it instantly
    # NOTE: I chose to hide the results window instead of closing it so that ImageJ does not prompt the user to save their results

    IJ.run("Close All") # Close all images
    return results # Return the results of the analysis

def save_rois (path,roi_names,image_name):
    # Function that saves the open ROIs in ImageJ to the inputted path as the inputted name, renaming the individual rois to their names
    roi_manager = RoiManager.getInstance() # Load the ROI manager
    
    for i,name in enumerate(roi_names):
        # Loop through each roi name
        roi_manager.rename(i,name)

    full_path = os.path.join(path,image_name + ".zip") # Combine the folder path and image name to create the full path to where the ROI will be saved

    roi_manager.runCommand("Save",full_path) # Save the ROIs to this path

    roi_manager.reset() # Clears the ROIs from the manager

def close_window(name):
    # Function to close a window in ImageJ given its name

    for frame in Frame.getFrames():
        # Get all actively open frames (windows) and loop through the
        if frame.getTitle() == name:
            # If the desired frame is in the list of open frames
            frame.dispose() # Dispose of it
            IJ.log(name+" was disposed.")
    # NOTE: I used the Frame class because ImageJ's WindowManager class does not include the Console window