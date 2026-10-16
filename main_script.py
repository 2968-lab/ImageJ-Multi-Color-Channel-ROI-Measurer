# This is the main script that performs the image analysis

import sys
import os
from ij import IJ 
from java.io import File

# Add directory path to sys.path so modules can be imported
fiji_dir = IJ.getDirectory("imagej") # Pull the path to imageJ
current_dir = os.path.join(fiji_dir, "plugins", "Take_ROI_Measurements") # Add the plugins and Take_ROI_Measurements directories to the path

if current_dir not in sys.path:
    # If this directory is not in the system paths (that would be searched for modules)
    sys.path.insert(0, current_dir) # Add it and set it as the first one (highest priority)

import imageJInterfacer # Import functions from the imagej interfacer script
import fileManager # Import functions from the file manager

# First, import configurations from config
config = fileManager.load_config(current_dir)

def run_script():
    # The script is wrapped in a function so that it can be easily exited if any information is missing or inaccurate
    # Next, check whether an image is open or can be opened
    [is_image_open,path_to_image] = imageJInterfacer.check_open_image()
    if is_image_open:
        # If an image is opened
        config.path = path_to_image # Update the config's path
    else:
        # If an image is not already open
        opened = False # Initialize opened flag as false
        if config.path != "":
            # If a path is listed in the config
            opened = imageJInterfacer.open_image(config.path) # Open the image
        if not opened:
            # If the image is not opened
            IJ.log("Error: No image open and no valid path recorded. Please open an image or fill in the file path.") # Inform the user
            return

    # Next, check whether an appropriate number of roi's are open
    if not imageJInterfacer.check_rois(config.roi_name):
        # If inapplicable roi's are open
        return # End the script

    # If rois look fine, run the analysis
    results = imageJInterfacer.run_analysis(config) # Begin the analysis

    if results is None:
        # If the analysis failed, stop
        return

    # Next, save the results and update config
    fileManager.save_results(config,results)

    # Once analysis is complete, save the ROIs
    roi_path = fileManager.get_roi_folder(config.path)
    image_name = os.path.basename(File(os.path.dirname(config.path)).getCanonicalPath()) # Get the cononical name of the image folder
    imageJInterfacer.save_rois(roi_path,config.roi_name,image_name) # Save the open ROIs to the ROI directory under the name of the image folder 

    if config.next_image:
        # Next, if the user wants to automatically open the next image, update the config's path to the next image
        if fileManager.transition_path(config,current_dir):
            # If the end of the image folder has been reached or the current folder could not be found or an eligible image could not be found in the next folder
            return # End the script
    
    # Finally, open the logged image (either the current or next image based on the user's input)
    imageJInterfacer.open_image(config.path)

    # Sometimes a threading error can pop up in the console even if everything exectued correctly.
    # If this point in the script is executing, then no error occured, and the console window can be closed.
    imageJInterfacer.close_window("Console") # Close the console window

if __name__ == "__main__":
    # If this file is being called directly
    run_script() # Run the script