import math

import numpy as np
from scipy.signal import butter, filtfilt, lfilter, firwin
import transforms3d
from .const import EARLY_STANCE, MIDDLE_STANCE, LATE_STANCE, SWING, EULER_INIT_LEN


class FPA:

    def __init__(self, is_right_foot, datarate=100, alpha=0.8):
        """
        @input: is_right_foot, bool value, True = sensor put on the right foot
                False = sensor put on the left foot
        @input: datarate, the update rate, unit is Hz.
        """
        self.datarate = datarate
        self.ALPHA = alpha
        self.FPA_this_step = 0.0
        self.FPA_last_step = 0.0
        self.step_data_buffer = []
        self.is_right_foot = is_right_foot

    # Calculate the foot progression angle
    def update_FPA(self, data, gaitphase_old, gaitphase):

        self.step_data_buffer.append(data)
        if gaitphase_old == EARLY_STANCE and gaitphase == MIDDLE_STANCE:
            euler_angles_esti = self.get_euler_angles(
                self.step_data_buffer, self.datarate
            )
            acc_rotated = self.get_rotated_acc(self.step_data_buffer, euler_angles_esti)
            acc_rotated_smoothed = self.smooth_acc_rotated(acc_rotated)
            self.FPA_this_step = self.get_FPA_via_max_acc_ratio_at_norm_peak(
                acc_rotated_smoothed
            )
            if self.FPA_this_step > 90:
                self.FPA_this_step = self.FPA_this_step - 180
            elif self.FPA_this_step < -90:
                self.FPA_this_step = self.FPA_this_step + 180
            self.step_data_buffer = []
            if self.is_right_foot:
                self.FPA_this_step = -self.FPA_this_step
            else:
                self.FPA_this_step = self.FPA_this_step

            # filter
            self.FPA_this_step = (
                self.FPA_this_step * self.ALPHA + (1 - self.ALPHA) * self.FPA_last_step
            )
            self.FPA_last_step = self.FPA_this_step

    @staticmethod
    def get_euler_angles(data_buffer, datarate):
        delta_t = 1 / datarate
        data_len = len(data_buffer)
        euler_angles_esti = np.zeros([data_len, 3])

        """1. initialize using the last couple samples"""
        gravity_vector = np.zeros([3])
        for i_sample in range(-1, -(EULER_INIT_LEN + 1), -1):
            sample_data = data_buffer[i_sample]
            gravity_vector += np.array(
                [sample_data["AccelX"], sample_data["AccelY"], sample_data["AccelZ"]]
            )
        gravity_vector /= EULER_INIT_LEN
        init_sample = data_len - math.ceil(EULER_INIT_LEN / 2)
        euler_angles_esti[init_sample:, 0] = np.arctan2(
            gravity_vector[1], gravity_vector[2]
        )  # axis 0
        euler_angles_esti[init_sample:, 1] = np.arctan2(
            -gravity_vector[0], np.sqrt(gravity_vector[1] ** 2 + gravity_vector[2] ** 2)
        )  # axis 1

        """2. Gyr integration"""
        for i_sample in range(init_sample - 1, -1, -1):
            sample_data = data_buffer[i_sample]
            sample_gyr = np.deg2rad(
                [sample_data["GyroX"], sample_data["GyroY"], sample_data["GyroZ"]]
            )

            roll, pitch, yaw = euler_angles_esti[i_sample + 1, :]
            transfer_mat = np.mat(
                [
                    [1, np.sin(roll) * np.tan(pitch), np.cos(roll) * np.tan(pitch)],
                    [0, np.cos(roll), -np.sin(roll)],
                    [0, np.sin(roll) / np.cos(pitch), np.cos(roll) / np.cos(pitch)],
                ]
            )
            angle_augment = np.matmul(transfer_mat, sample_gyr)
            euler_angles_esti[i_sample, :] = (
                euler_angles_esti[i_sample + 1, :] - angle_augment * delta_t
            )

        return euler_angles_esti

    @staticmethod
    def smooth_acc_rotated(acc_rotated, smooth_win_len=29):
        data_len = acc_rotated.shape[0]

        acc_rotated_smoothed = np.zeros(acc_rotated.shape)
        smooth_win_len = min(data_len, smooth_win_len)
        for i_axis in range(2):
            acc_rotated_smoothed[:, i_axis] = FPA.smooth(
                acc_rotated[:, i_axis], smooth_win_len, "hanning"
            )
        return acc_rotated_smoothed

    @staticmethod
    def get_FPA_via_max_acc_ratio_at_norm_peak(acc_rotated):
        step_sample_num = acc_rotated.shape[0]
        peak_check_start = int(0.56 * step_sample_num)
        acc_second_half = acc_rotated[peak_check_start:, :]
        planar_acc_norm = np.linalg.norm(acc_second_half[:, :2], axis=1)
        max_acc_norm = np.argmax(planar_acc_norm)
        max_acc = acc_second_half[max_acc_norm, :]
        FPA_estis = np.arctan2(max_acc[0], max_acc[1]) * 180 / np.pi
        return FPA_estis

    @staticmethod
    def get_rotated_acc(step_data_buffer, euler_angles):
        data_len = len(step_data_buffer)
        acc_rotated = np.zeros([data_len, 3])
        for i_sample, sample_data in enumerate(step_data_buffer):
            sample_acc = [
                sample_data["AccelX"],
                sample_data["AccelY"],
                sample_data["AccelZ"],
            ]
            dcm_mat = transforms3d.euler.euler2mat(
                euler_angles[i_sample, 0], euler_angles[i_sample, 1], 0
            )
            acc_rotated[i_sample, :] = np.matmul(dcm_mat, sample_acc)
        return acc_rotated

    @staticmethod
    def data_filt(data, cut_off_fre=3.8, sampling_fre=100, filter_order=4):
        fre = cut_off_fre / (sampling_fre / 2)
        b, a = butter(filter_order, fre, "lowpass")
        if len(data.shape) == 1:
            data_filt = filtfilt(b, a, data)
        else:
            data_filt = filtfilt(b, a, data, axis=0)
        return data_filt

    @staticmethod
    def smooth(x, window_len, window):

        window_fuction_dict = {
            "flat": np.ones(window_len, "d"),
            "hanning": np.hanning(window_len),
            "hamming": np.hamming(window_len),
            "bartlett": np.bartlett(window_len),
            "blackman": np.blackman(window_len),
        }

        w = window_fuction_dict[window]
        y = np.convolve(w / w.sum(), x, mode="same")
        return y
