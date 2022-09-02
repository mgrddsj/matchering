import matchering as mg


# Sending all log messages to the default print function
# Just delete the following line to work silently
mg.log(print)

mg.process(
    # The track you want to master
    target="examples\\20062022035056.mp3",
    # Some "wet" reference track
    reference="examples\ellie.mp3",
    # Where and how to save your results
    results=[
        #mg.pcm16("my_song_master_16bit.wav"),
        mg.Result(
            "examples\\test.mp3","LAME", use_limiter=True, normalize=True,
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
        # Change the temp folder to work with ffmpeg
        # temp_folder="/tmp",
        # Lower the preview length to 15 seconds from the default value of 30
        # preview_size=15,
        # Allow matchering to accept the same files (useless in fact)
        # allow_equality=True
        # high_filter = 800, in Hz
        # low_filter = 200, in Hz
        # Etc...
        # The remaining parameters will be filled with default values
        # Examine defaults.py to find other parameters
    ),
    preview_target = mg.Result(
            "examples\\target.mp3","LAME", use_limiter=True, normalize=True,
            no_eq= False
        ),
    preview_result = mg.Result(
            "examples\\preview.mp3","LAME", use_limiter=True, normalize=True,
            no_eq= False
        ),
)
