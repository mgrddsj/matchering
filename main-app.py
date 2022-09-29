
import matchering as mg
# web service variation
from flask import Flask, request
from flask_cors import CORS

from matchering.loader import delete_temp, get_temp_name, load_binary, save_temp

# any name will work for internal identification
app = Flask(__name__)
CORS(app)

@app.route('/matchering',methods=['GET','POST'])
    # methods go here
def matchering():

    data = request.files['song']  # parse arguments to dictionary
    
    temp_folder = "download"
    result_folder = "result"
    temp_file, file_ext, file_path = get_temp_name(data.filename, temp_folder)
    data.save(file_path)
    # Sending all log messages to the default print function
    # Just delete the following line to work silently
    mg.log(print)
    mg.process(
        # The track you want to master
        target=temp_folder + "\\" + temp_file,
        # Some "wet" reference track
        reference="",
        # Where and how to save your results
        results=[
            #mg.pcm16("my_song_master_16bit.wav"),
            mg.Result(
                result_folder + "\\" + temp_file,"LAME" if file_ext == "MP3" else "PCM_24", 
                use_limiter=True, normalize=True, no_eq= False
            ),
        ],
        # Create a custom Config instance to edit matchering configuration
        # Think twice before you change something here
        config=mg.Config(
            fft_size= 8192,
            # Change the temp folder to work with ffmpeg
            # temp_folder="/tmp",
            reference_processed = True,
            reference_preset = True,
            # high_filter = 800, in Hz
            # low_filter = 200, in Hz
            # Etc...
            # The remaining parameters will be filled with default values
            # Examine defaults.py to find other parameters
        ),
    )
    result = load_binary(temp_file, result_folder)
    delete_temp(temp_file,temp_folder)
    delete_temp(temp_file,result_folder)

    return result, 200  # return data with 200 OK

if __name__ == '__main__':
    app.run(debug=True)  # run our Flask app

