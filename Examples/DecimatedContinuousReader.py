import sys
sys.path.append(r'..')
from PhoenixGeoPy.Reader.TimeSeries import DecimatedContinuousReader
from matplotlib.pyplot import plot, draw, title, pause, clf
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
    if len(sys.argv) < 2:
        print("Usage:\n" + str(sys.argv[0]) + " <pathToDecimatedSegmentedFile>.td_150")
        sys.exit(-1)

    # Open a reader for the file path passed as argument
    decimated_reader = DecimatedContinuousReader(sys.argv[1])

    # Obtain the data sample rate form the reader
    sample_rate = decimated_reader.header_info["sample_rate"]

    keep_running = True
    while (keep_running):
        # Read one second worth of data
        data = decimated_reader.read_data(sample_rate)
        if len(data) < sample_rate:
            keep_running = False
            break

        keep_running = plot_data(data)
