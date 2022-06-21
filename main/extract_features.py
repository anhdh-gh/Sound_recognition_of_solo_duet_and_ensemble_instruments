import librosa
import numpy as np
from numpy import number, empty, cos, sin
from numpy.fft import fft
from scipy.signal import find_peaks

from main.constants import HOP_LENGTH, FRAME_SIZE, SAMPLE_RATE


# Năng lượng trung bình
def average_energy(amplitude):
    N = len(amplitude)
    sum = 0
    for i in range(0, N, 1):
        sum = sum + amplitude[i] ** 2
    average_energy = sum / N
    return average_energy


# Tốc độ đổi dấu của tín hiệu
def zero_crossing_rate(amplitude):
    N = len(amplitude)
    sgn = lambda n: 1 if n > 0 else (0 if n == 0 else -1)

    sum = 0
    for i in range(1, N, 1):
        sum = sum + np.abs(sgn(amplitude[i]) - sgn(amplitude[i - 1]))

    return sum / (2 * N)


# Tỉ lệ khoảng lặng
# Nếu tồn tại time_threshold mẫu liên tiếp có giá trị biên độ <= amplitude_threshold thì coi các mẫu đó là im lặng
def silence_ratio(amplitude, amplitude_threshold, time_threshold):
    # Ta dựa vào ngưỡng amplitude_threshold để lấy ra các vị trí mà có các phần tử > amplitude_threshold
    indexs = np.array([-1])
    for i, x in enumerate(amplitude):
        if x > amplitude_threshold:
            indexs = np.append(indexs, i)
    indexs = np.append(indexs, len(amplitude))

    # Các index này sẽ chia mảng ra thành các khoảng mà trong các khoảng đó các giá trị biên độ liên tiếp đều <= amplitude_threshold
    # Đếm số lượng các mẫu trong các khoảng
    count_sample = 0
    for i in range(1, len(indexs), 1):
        number_sample = indexs[i] - indexs[i - 1] - 1
        if number_sample >= time_threshold:
            count_sample += number_sample

    # Tỉ lệ khoảng lặng = Tổng thời gian không có tiếng  / Thời gian của tệp âm thanh
    return count_sample / len(amplitude)


# Ví dụ về thuật toán tìm các dãy có liên tiếp có các phần tử đều <= k
# array = [1, 9, 4, 3, 6, 5, 7, 3, 5, 8, 0, 2, 5, 1, 5, 8, 3]
# k = 7
# => indexs = [-1, 1, 9, 15, 17]
# => ta thu được các khoảng
#       [1] <=> (-1, 1) <=> [0 , 1)
#       [4, 3, 6, 5, 7, 3, 5] <=> (1, 9)
#       [0, 2, 5, 1, 5] <=> (9, 15)
#       [3] <=> (15, 17)
# Tính số lượng phần của của 1 dãy
#     (cuối - đầu)/khoảng cách + 1
# Đối với bài này do khoảng là (đầu, cuối)
# => ((cuối - 1) - (đầu - 1))/1 + 1 = cuối - đầu - 1


# Biến đổi Fourier rời rạc (DFT)
def dft(amplitude):
    # e^(-j2πnk/N) = cos(2πnk/N) - j.sin(2πnk/N)
    # N = len(amplitude)
    # dft_value = np.array(empty(N, dtype=complex))
    #
    # for k in range(0, N, 1):
    #     sum = 0 + 0j
    #     for n, v in enumerate(amplitude):
    #         sum = sum + (v * complex(cos((2 * k * np.pi * n)/N), -sin((2 * k * np.pi * n)/N)))
    #     dft_value[k] = sum

    dft_value = fft(amplitude)
    return dft_value


# Lấy ra số lượng tần số
def find_frequencies(frequencies, magnitude_spectrum):
    # Đỉnh phải có độ lớn tối thiểu là height và các đỉnh lân cận phải cách nhau ít nhất distance
    index, _ = find_peaks(
        magnitude_spectrum,
        height=np.max(magnitude_spectrum) * 0.03,
        distance=50
    )

    # Các tần số dưới 20 Hz coi là nhiễu
    new_index = np.array([], dtype=np.int64)
    for i in index:
        if 20 <= frequencies[i]:
            new_index = np.append(new_index, i)
    index = new_index

    return frequencies[index]
