
from asyncio import threads
import matchering as mg
import logging
# web service variation
from flask import Flask, request
from flask_cors import CORS

from matchering.loader import delete_temp, get_temp_name, load_binary, save_temp
from matchering.utils import debugger_is_active

# any name will work for internal identification
app = Flask(__name__)
CORS(app)

@app.route('/matchering',methods=['GET','POST'])

    # methods go here
def matchering():

    try:
        
        data = request.files['song']  # parse arguments to dictionary
        noEQ = request.form['noEQ']
        
        temp_folder = "download"
        result_folder = "result"
        temp_file, file_ext, file_path = get_temp_name(data.filename, temp_folder)
        data.save(file_path)

        logging.info("starting process")
        
            
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
                    use_limiter=True, normalize=True, no_eq= True if noEQ == 'true' else False
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
        logging.info("process done")
        result = load_binary(temp_file, result_folder)
        delete_temp(temp_file,temp_folder)
        delete_temp(temp_file,result_folder)

        return result, 200  # return data with 200 OK
    except RuntimeError as e:
        logging.error(e)
        e = str(e)
        return e, 500


if __name__ == '__main__':
    # Sending all log messages to the default print function
    # Just delete the following line to work silently
    if mg.utils.debugger_is_active():
        mg.log(print)
    else:
        logging.basicConfig(filename="log.txt", level=logging.INFO)
        mg.log(logging.debug)
        mg.log(info_handler=logging.info)
        mg.log(warning_handler=logging.warning)
              
    # run our Flask app
    from waitress import serve
    serve(app, host="127.0.0.1", port=5001, threads=1)
    # app.run(debug=False)  

