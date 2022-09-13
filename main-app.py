from unittest import result
import matchering as mg
# web service variation
from flask import Flask
from flask_restful import Resource, Api, reqparse

from matchering.loader import load_binary, save_temp

# any name will work for internal identification
app = Flask(__name__)
api = Api(app)

class Matchering(Resource):
    # methods go here
    def post(self):

        parser = reqparse.RequestParser()  # initialize

        parser.add_argument('song', required=True)  # add arguments

        args = parser.parse_args()  # parse arguments to dictionary
        temp_folder = "\\download"
        result_folder = "\\result"
        temp_file = save_temp(args['song'], temp_folder)
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
                    result_folder + "\\" + temp_file,"LAME", 
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

        return {'data': load_binary(temp_file, result_folder)}, 200  # return data with 200 OK
    pass

api.add_resource(Matchering, '/matchering') 
if __name__ == '__main__':
    app.run(debug=True)  # run our Flask app

