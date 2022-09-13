import matchering as mg
from os import walk
import argparse

parser = argparse.ArgumentParser(description='Batch convert an input folder of music to an output folder')
parser.add_argument("input", type=str, help="Input folder path (absolute or relative)")
parser.add_argument("output", type=str, help="Output folder path (absolute or relative)")
parser.add_argument("--ref", type=str, default="", help='(Optional) Some "wet" reference track')
parser.add_argument("--proc", type=bool, default=True, help='(Optional) if the reference track is a well selected loud section instead of a complete song')
args = parser.parse_args()

# Sending all log messages to the default print function
# Just delete the following line to work silently
mg.log(print)
for root, dirs, files in walk(args.input):
    for name in files:
        mg.process(
            # Set the folder to read from
            target=args.input + "\\" + name,
            # Some "wet" reference track
            reference=args.ref,
            # Set the folder to save to
            results=[
                #mg.pcm16("my_song_master_16bit.wav"),
                mg.Result(
                    args.output + "\\" + name,"LAME", use_limiter=True, normalize=True,
                    no_eq= False
                ),
            ],
            # Create a custom Config instance to edit matchering configuration
            # Think twice before you change something here
            config=mg.Config(
                # Increase the maximum length to 30 minutes from the default value of 15
                # max_length=30 * 60,
                # Increase the internal and resulting sample rate to 96 kHz from the default value of 44.1 kHz
                # internal_sample_rate=96000,
                # Change the threshold value (float, not dB) from the default value of 0.9981 (-0.01 dB)
                # threshold=0.7079,  # -3 dB
                fft_size= 8192,
                # Change the temp folder to work with ffmpeg
                # temp_folder="/tmp",
                # Lower the preview length to 15 seconds from the default value of 30
                # preview_size=15,
                # Allow matchering to accept the same files (useless in fact)
                # allow_equality=True
                reference_processed = args.proc,
                reference_preset = True if args.ref == "" else False,
                # high_filter = 800, in Hz
                # low_filter = 200, in Hz
                # Etc...
                # The remaining parameters will be filled with default values
                # Examine defaults.py to find other parameters
            )
            )
""" preview_target = mg.Result(
        "examples\\original.mp3","LAME", use_limiter=True, normalize=True,
        no_eq= False
    ),
preview_result = mg.Result(
        "examples\\preview.mp3","LAME", use_limiter=True, normalize=True,
        no_eq= False
    ), """

