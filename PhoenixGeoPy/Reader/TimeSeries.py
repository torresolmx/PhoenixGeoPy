"""Module to read and parse native Phoenix Geophysics data formats of the MTU-5C Family

This module implements Streamed readers for segmented-decimated continuus-decimated
and native sampling rate time series formats of the MTU-5C family.
"""

__author__ = 'Jorge Torres-Solis'

from numpy import empty, fromfile, float32, append
from struct import unpack_from, unpack
import os
import string
from cmath import phase
from DataScaling import DataScaling


class _TSReaderBase(object):
    def __init__(self, path, num_files=1, header_size=128, report_hw_sat=False):
        self.base_path = path
        self.base_dir, self.file_name = os.path.split(self.base_path)
        file_name_base, self.file_extension = self.file_name.split(".", 2)
        file_parts = file_name_base.split("_")
        self.inst_id = file_parts[0]
        self.rec_id = file_parts[1]
        self.ch_id = file_parts[2]
        seq_str = file_parts[3]
        self.seq = int(seq_str, base=16)
        self.last_seq = self.seq + num_files
        self.stream = None
        self.report_hw_sat = report_hw_sat
        self.header_info = {}
        self.header_size = header_size
        self.dataHeader = None
        self.open_file_seq(self.seq)   # Open the file passed as the fisrt file in the sequence to stream
        self.ad_plus_minus_range = 5.0  # differential voltage range that the A/D can measure (Board model dependent)
        self.channel_type = "?"           # "E" or "H"
        self.channel_main_gain = None     # The value of the main gain of the board
        self.intrinsic_circuitry_gain = None  # Circuitry Gain not directly configurable by the user
        self.total_circuitry_gain = None  # Total board Gain both intrinsic gain and user-seletable gain in circuit
        self.total_selectable_gain = None  # Total of the gain that is selectable by the user (i.e. att * pre * gain)
        self.lpf_Hz = None                   # Nominal cutoff freq of the configured LPF of the channel
        self.preamp_gain = 1.0
        self.attenuator_gain = 1.0

    def open_next(self):
        ret_val = False
        if self.stream is not None:
            self.stream.close()
        self.seq += 1
        if self.seq < self.last_seq:
            new_seq_str = "%08X" % (self.seq)
            new_path = (self.base_dir + '/' + self.inst_id + '_' +
                        self.rec_id + '_' + self.ch_id + '_' +
                        new_seq_str + '.' + self.file_extension)
            if os.path.exists(new_path):
                self.stream = open(new_path, 'rb')
                if self.header_size > 0:
                    self.dataHeader = self.stream.read(self.header_size)
                ret_val = True

        return ret_val

    def open_file_seq(self, file_seq_num):
        ret_val = False
        if self.stream is not None:
            self.stream.close()
        self.seq = file_seq_num
        new_seq_str = "%08X" % (self.seq)
        new_path = (self.base_dir + '/' + self.inst_id + '_' +
                    self.rec_id + '_' + self.ch_id + '_' +
                    new_seq_str + '.' + self.file_extension)
        if os.path.exists(new_path):
            print (" opening " + new_path)
            self.stream = open(new_path, 'rb')
            if self.header_size > 0:
                self.dataHeader = self.stream.read(self.header_size)
            ret_val = True

        return ret_val

    def __populate_channel_type(self, config_fp):
        if config_fp[1] & 0x08 == 0x08:
            self.channel_type = "E"
        else:
            self.channel_type = "H"
        # Channel type detected by electronics
        # this normally matches self.channel_type, but used in electronics design and testing
        if config_fp[1] & 0x20 == 0x20:
            self.detected_channel_type = 'E'
        else:
            self.detected_channel_type = 'H'

    def __populate_lpf(self, config_fp):
        if config_fp[0] & 0x80 == 0x80:            # LPF on
            if config_fp[0] & 0x03 == 0x03:
                self.lpf_Hz = 10
            elif config_fp[0] & 0x03 == 0x02:
                if (self.board_model_main == "BCM03" or self.board_model_main == "BCM06"):
                    self.lpf_Hz = 1000
                else:
                    self.lpf_Hz = 100
            elif config_fp[0] & 0x03 == 0x01:
                if (self.board_model_main == "BCM03" or self.board_model_main == "BCM06"):
                    self.lpf_Hz = 10000
                else:
                    self.lpf_Hz = 1000
        else:                                      # LPF off
            if (self.board_model_main == "BCM03" or self.board_model_main == "BCM06"):
                self.lpf_Hz = 17800
            else:
                self.lpf_Hz = 10000

    def __popuate_peamp_gain(self, config_fp):
        if self.channel_type == "?":
            raise Exception("Channel type must be set before attemting to calculate preamp gain")
        preamp_on = bool(config_fp[0] & 0x10)
        self.preamp_gain = 1.0
        if self.channel_type == "E":
            if preamp_on is True:
                if self.board_model_main == "BCM01" or self.board_model_main == "BCM03":
                    self.preamp_gain = 4.0
                    if (self.board_model_revision == "L"):
                        #Account for BCM01-L experimental prototype
                        self.preamp_gain = 8.0
                else:
                    self.preamp_gain = 8.0
                    # Acount for experimental prototype BCM05-A
                    if self.header_info['ch_hwv'][0:7] == "BCM05-A":
                        self.preamp_gain = 4.0
    
    def __populate_main_gain(self, config_fp):
        # BCM05-B and BCM06 introduced different selectable gains
        new_gains = True   # we asume any newer board will have the new gain banks
        if self.board_model_main == "BCM01" or self.board_model_main == "BCM03":
            # Original style 24 KSps boards and original 96 KSps boards
            new_gains = False
        if self.header_info['ch_hwv'][0:7] == "BCM05-A":
            # Acount for experimental prototype BCM05-A, which also had original gain banks
            new_gains = False
        if config_fp[0] & 0x0C == 0x00:
            self.channel_main_gain = 1.0
        elif config_fp[0] & 0x0C == 0x04:
            self.channel_main_gain = 4.0
        elif config_fp[0] & 0x0C == 0x08:
            self.channel_main_gain = 6.0
            if not new_gains:
                self.channel_main_gain = 16.0
        elif config_fp[0] & 0x0C == 0x0C:
            self.channel_main_gain = 8.0
            if not new_gains:
                self.channel_main_gain = 32.0

    def __handle_sensor_range(self, config_fp):
        """This function will adjust the intrinsic circuitry gain based on the
           sensor range configuration in the configuration fingerprint
           
           For this, we consider that for the Electric channel, calibration path, or H-legacy
           sensors all go through a 1/4 gain stage, and then they get a virtial x2 gain from
           Single-ended-diff before the A/D. In the case of newer sensors (differential)
           instead of a 1/4 gain stage, there is only a 1/2 gain stage
           
           Therefore, in the E,cal and legacy sensor case the circuitry gain is 1/2, while for
           newer sensors it is 1
           """
        if self.channel_type == "?":
            raise Exception("Channel type must be set before attemting to calculate preamp gain")
        self.intrinsic_circuitry_gain = 0.5   
        if self.channel_type == "H":
            if config_fp[1] & 0x01 == 0x01:
                self.intrinsic_circuitry_gain = 1.0

    def __populate_attenuator_gain(self, config_fp):
        self.attenuator_gain = 1.0    # Asume attenuator off
        if self.channel_type == "?":
            raise Exception("Channel type must be set before attemting to calculate preamp gain")
        attenuator_on = bool(config_fp[4] & 0x01)
        if attenuator_on and self.channel_type == "E":
            new_attenuator = True  # By default assume that we are dealing with a newer types of boards
            if self.board_model_main == "BCM01" or self.board_model_main == "BCM03":
                # Original style 24 KSps boards and original 96 KSps boards
                new_attenuator = False
            if self.header_info['ch_hwv'][0:7] == "BCM05-A":
                # Acount for experimental prototype BCM05-A, which also had original gain banks
                new_attenuator = False

            if new_attenuator:
                self.attenuator_gain = 523.0 / 5223.0
            else:
                self.attenuator_gain = 0.1

    def unpack_header(self):
        self.header_info['file_type'] = unpack_from('B', self.dataHeader, 0)[0]
        self.header_info['file_version'] = unpack_from('B', self.dataHeader, 1)[0]
        self.header_info['length'] = unpack_from('H', self.dataHeader, 2)[0]
        self.header_info['inst_type'] = unpack_from('8s', self.dataHeader, 4)[0].decode("utf-8").strip(' ').strip('\x00')
        self.header_info['inst_serial'] = b''.join(unpack_from('cccccccc', self.dataHeader, 12)).strip(b'\x00')
        self.header_info['rec_id'] = unpack_from('I', self.dataHeader, 20)[0]
        self.header_info['ch_id'] = unpack_from('B', self.dataHeader, 24)[0]
        self.header_info['file_sequence'] = unpack_from('I', self.dataHeader, 25)[0]
        self.header_info['frag_period'] = unpack_from('H', self.dataHeader, 29)[0]
        self.header_info['ch_hwv'] = unpack_from('8s', self.dataHeader, 31)[0].decode("utf-8").strip(' ')
        self.board_model_main = self.header_info['ch_hwv'][0:5]
        self.board_model_revision = self.header_info['ch_hwv'][6:1]
        self.header_info['ch_ser'] = unpack_from('8s', self.dataHeader, 39)[0].decode("utf-8").strip('\x00')
        # handle the case of backend < v0.14, which puts '--------' in ch_ser
        if all(chars in string.hexdigits for chars in self.header_info['ch_ser']):
            self.header_info['ch_ser'] = int(self.header_info['ch_ser'], 16)
        else:
            self.header_info['ch_ser'] = 0
        self.header_info['ch_fir'] = hex(unpack_from('I', self.dataHeader, 47)[0])
        config_fp = unpack_from('BBBBBBBB', self.dataHeader, 51)
        self.header_info['conf_fp'] = config_fp
        # Channel type
        self.__populate_channel_type(config_fp)
        # Electric channel Preamp
        self.__popuate_peamp_gain(config_fp)
        # LPF
        self.__populate_lpf(config_fp)
        # Main Gain Stage
        self.__populate_main_gain(config_fp)
        # Sensor range
        self.__handle_sensor_range(config_fp)
        # Electric channel attenuator
        self.__populate_attenuator_gain(config_fp)
        # Board-wide gains
        self.total_selectable_gain = self.channel_main_gain * self.preamp_gain * self.attenuator_gain
        self.total_circuitry_gain = self.total_selectable_gain * self.intrinsic_circuitry_gain

        self.header_info['sample_rate_base'] = unpack_from('H', self.dataHeader, 59)[0]
        self.header_info['sample_rate_exp'] = unpack_from('b', self.dataHeader, 61)[0]
        self.header_info['sample_rate'] = self.header_info['sample_rate_base']
        if self.header_info['sample_rate_exp'] != 0:
            self.header_info['sample_rate'] *= pow(10, self.header_info['sample_rate_exp'])
        self.header_info['bytes_per_sample'] = unpack_from('B', self.dataHeader, 62)[0]
        self.header_info['frame_size'] = unpack_from('I', self.dataHeader, 63)[0]
        self.dataFooter = self.header_info['frame_size'] >> 24
        self.frameSize = self.header_info['frame_size'] & 0x0ffffff
        self.header_info['decimation_node_id'] = unpack_from('H', self.dataHeader, 67)[0]
        self.header_info['frame_rollover_count'] = unpack_from('H', self.dataHeader, 69)[0]
        self.header_info['gps_long'] = unpack_from('f', self.dataHeader, 71)[0]
        self.header_info['gps_lat'] = unpack_from('f', self.dataHeader, 75)[0]
        self.header_info['gps_height'] = unpack_from('f', self.dataHeader, 79)[0]
        self.header_info['gps_hacc'] = unpack_from('I', self.dataHeader, 83)[0]
        self.header_info['gps_vacc'] = unpack_from('I', self.dataHeader, 87)[0]
        self.header_info['timing_status'] = unpack_from('BBH', self.dataHeader, 91)
        self.header_info['timing_flags'] = self.header_info['timing_status'][0]
        self.header_info['timing_sat_count'] = self.header_info['timing_status'][1]
        self.header_info['timing_stability'] = self.header_info['timing_status'][2]
        self.header_info['future1'] = unpack_from('b', self.dataHeader, 95)[0]
        self.header_info['future2'] = unpack_from('i', self.dataHeader, 97)[0]
        self.header_info['saturated_frames'] = unpack_from('H', self.dataHeader, 101)[0]
        if self.header_info['saturated_frames'] & 0x80 == 0x80:
            self.header_info['saturated_frames'] &= 0x7F
            self.header_info['saturated_frames'] <<= 4
        self.header_info['missing_frames'] = unpack_from('H', self.dataHeader, 103)[0]
        self.header_info['battery_voltage_mV'] = unpack_from('H', self.dataHeader, 105)[0]
        self.header_info['min_signal'] = unpack_from('f', self.dataHeader, 107)[0]
        self.header_info['max_signal'] = unpack_from('f', self.dataHeader, 111)[0]

    def close(self):
        if self.stream is not None:
            self.stream.close()

class NativeReader(_TSReaderBase):
    """Native sampling rate 'Raw' time series reader class"""

    def __init__(self, path, num_files=1, scale_to=DataScaling.AD_input_volts,
                 header_size=128, last_frame=0, channel_gain=0.5, ad_plus_minus_range = 5.0,
                 channel_type="E", report_hw_sat=False):
        # Init the base class
        _TSReaderBase.__init__(self, path, num_files, header_size, report_hw_sat)

        # Track the last frame seen by the streamer, to report missing frames
        self.last_frame = last_frame
        self.header_size = header_size
        self.data_scaling = scale_to
        self.total_circuitry_gain = channel_gain
        self.ad_plus_minus_range = ad_plus_minus_range

        if header_size == 128:
            self.unpack_header()

        # Now that we have the channel circuit-based gain (either form init or from the header)
        # We can calculate the voltage range at the input of the board.
        self.input_plusminus_range = self.ad_plus_minus_range / self.total_circuitry_gain

        if self.data_scaling == DataScaling.AD_in_ADunits:
            self._scale_factor = 256
        elif self.data_scaling == DataScaling.AD_input_volts:
            self._scale_factor = self.ad_plus_minus_range / (2 ** 31)
        elif self.data_scaling == DataScaling.instrument_input_volts:
            self._scale_factor = self.input_plusminus_range / (2 ** 31)
        else:
            raise LookupError("Invalid scaling requested")

        # optimization variables
        self.footer_idx_samp_mask = int('0x0fffffff', 16)
        self.footer_sat_mask = int('0x70000000', 16)

    def unpack_header(self):
        super(NativeReader, self).unpack_header()
        # TODO: Implement any specific header unpacking for this particular class below

    def read_frames(self, num_frames):
        frames_in_buf = 0
        _idx_buf = 0
        _data_buf = empty([num_frames * 20])  # 20 samples packed in a frame

        while (frames_in_buf < num_frames):

            dataFrame = self.stream.read(64)
            if not dataFrame:
                if not self.open_next():
                    return empty([0])
                dataFrame = self.stream.read(64)
                if not dataFrame:
                    return empty([0])

            dataFooter = unpack_from("I", dataFrame, 60)

            # Check that there are no skipped frames
            frameCount = dataFooter[0] & self.footer_idx_samp_mask
            difCount = frameCount - self.last_frame
            if (difCount != 1):
                print ("Ch [%s] Missing frames at %d [%d]\n" %
                       (self.ch_id, frameCount, difCount))
            self.last_frame = frameCount

            for ptrSamp in range(0, 60, 3):
                tmpSampleTupple = unpack(">i", dataFrame[ptrSamp:ptrSamp + 3] + b'\x00')
                _data_buf[_idx_buf] = tmpSampleTupple[0] * self._scale_factor
                _idx_buf += 1

            frames_in_buf += 1

            if self.report_hw_sat:
                satCount = (dataFooter[0] & self.footer_sat_mask) >> 24
                if satCount:
                    print ("Ch [%s] Frame %d has %d saturations" %
                           (self.ch_id, frameCount, satCount))

        return _data_buf

    def skip_frames(self, num_frames):
        bytes_to_skip = int(num_frames * 64)
        # Python is dumb for seek and tell, it cannot tell us if a seek goes
        # past EOF so instead we need to do inefficient reads to skip bytes
        while (bytes_to_skip > 0):
            foo = self.stream.read(bytes_to_skip)
            local_read_size = len(foo)

            # If we ran out of data in this file before finishing the skip,
            # open the next file and return false if there is no next file
            # to indicate that the skip ran out of
            # data before completion
            if local_read_size == 0:
                more_data = self.open_next()
                if not more_data:
                    return False
            else:
                bytes_to_skip -= local_read_size

        # If we reached here we managed to skip all the data requested
        # return true
        self.last_frame += num_frames
        return True


class DecimatedSegmentedReader(_TSReaderBase):
    """Class to create a streamer for segmented decimated time series,
       i.e. *.td_24k"""
    def __init__(self, path, num_files=1, report_hw_sat=False):
        # Init the base class
        _TSReaderBase.__init__(self, path, num_files, 128, report_hw_sat)
        self.unpack_header()
        self.subheader = {}

    def unpack_header(self):   # TODO: Work in progress, for now unpacking as raw time series header
        if self.header_size == 128:
            super(DecimatedSegmentedReader, self).unpack_header()
            # TODO: Implement any specific header unpacking for this particular class below

    def read_subheader(self):
        subheaderBytes = self.stream.read(32)
        if not subheaderBytes:
            if self.open_next():
                subheaderBytes = self.stream.read(32)

        if not subheaderBytes or len(subheaderBytes) < 32:
            self.subheader['timestamp'] = 0
            self.subheader['samplesInRecord'] = 0
        else:
            self.subheader['timestamp'] = unpack_from('I', subheaderBytes, 0)[0]
            self.subheader['samplesInRecord'] = unpack_from('I', subheaderBytes, 4)[0]
            self.subheader['satCount'] = unpack_from('H', subheaderBytes, 8)[0]
            self.subheader['missCount'] = unpack_from('H', subheaderBytes, 10)[0]
            self.subheader['minVal'] = unpack_from('f', subheaderBytes, 12)[0]
            self.subheader['maxVal'] = unpack_from('f', subheaderBytes, 16)[0]
            self.subheader['avgVal'] = unpack_from('f', subheaderBytes, 20)[0]

    def read_record_data(self):
        ret_array = empty([0])
        if (self.stream is not None
                and self.subheader['samplesInRecord'] is not None
                and self.subheader['samplesInRecord'] != 0):
            ret_array = fromfile(self.stream, dtype=float32, count=self.subheader['samplesInRecord'])
            if ret_array.size == 0:
                if not self.open_next():
                    return empty([0])
                # Array below will contain the data, or will be an empty array if end of series as desired
                ret_array = fromfile(self.stream, dtype=float32, count=self.subheader['samplesInRecord'])

        return ret_array

    def read_record(self):
        self.read_subheader()
        return self.read_record_data()

class DecimatedContinuousReader(_TSReaderBase):
    """Class to create a streamer for continuous decimated time series,
    i.e. *.td_150, *.td_30"""
    def __init__(self, path, num_files=1, report_hw_sat=False):
        # Init the base class
        _TSReaderBase.__init__(self, path, num_files, 128, report_hw_sat)
        self.unpack_header()
        self.subheader = {}

    def unpack_header(self):   # TODO: Work in progress, for now unpacking as raw time series header
        if self.header_size == 128:
            super(DecimatedContinuousReader, self).unpack_header()
            # TODO: Implement any specific header unpacking for this particular class below

    def read_data(self, numSamples):
        ret_array = empty([0])
        if self.stream is not None:
            ret_array = fromfile(self.stream, dtype=float32, count=numSamples)
            while ret_array.size < numSamples:
                if not self.open_next():
                    return empty([0])
                # Array below will contain the data, or will be an empty array if end of series as desired
                ret_array = append(ret_array,
                                   fromfile(self.stream,
                                            dtype=float32,
                                            count=(numSamples - ret_array.size)))
        return ret_array
