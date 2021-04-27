import sys
sys.path.append(r'..')
from PhoenixGeoPy.Reader.TimeSeries import NativeReader
from matplotlib.pyplot import plot, draw, pause, clf
from numpy import linspace

def console_input(message):
    if sys.version_info[0] < 3:
        # Python 2 uses "raw_input()"
        return raw_input(message)
    else:
        return input(message)

# ========================================================================
def plot_data(data_samples):
    ts_start_sample = sample_rate * plot_data.second_read
    x_sample = linspace(ts_start_sample, ts_start_sample + sample_rate -1, sample_rate)
    clf()
    plot(x_sample, data)
    draw()
    pause(0.01)

    plot_data.second_read += 1

    # Ask in the console what to do next
    answer = console_input('Command? f=forward, x=exit\n')
    while answer != 'f' and answer != 'x':
        answer = console_input('Invalid input, Command? f=forward, x=exit\n')

    keep_reading = False
    if answer == 'f':
        keep_reading = True
    elif answer == 'x':
        keep_reading = False

    return keep_reading

plot_data.second_read=0

# ========================================================================
if __name__ == "__main__" and __package__ is None:
    # Open a reader for channel Ex (channel 1 in the data folder)
    ExReader = NativeReader("../Sample Data/10128_2021-04-27-025909/1/10128_60877DFD_1_00000001.bin")

    # Obtain the data sample rate form the reader
    sample_rate = ExReader.header_info["sample_rate"]

    frames_per_sec_at_24KSps = 1200


    keep_running = True
    while (keep_running):
        # Read one second worth of data
        data = ExReader.read_frames(frames_per_sec_at_24KSps)
        if len(data) < sample_rate:
            keep_running = False
            break

        keep_running = plot_data(data)