import math
import operator
import os
import shutil
import traceback
from pathlib import Path

import librosa
import numpy as np
import pandas as pd
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from matplotlib import pyplot as plt
from pyexpat import features

from main.constants import SAMPLE_RATE, HOP_LENGTH, FRAME_SIZE
from main.extract_features import average_energy, zero_crossing_rate, silence_ratio, dft, find_frequencies
from main.models import File, MusicalInstrument, Attribute, AttributeValue, Chart


def get_real_path(relative_path):
    fs = FileSystemStorage()
    path = fs.path(relative_path)
    return path


def get_relative_path(real_path):
    fs = FileSystemStorage()
    return fs.url(real_path)


def get_values_of_attribute(file, attribute_name):
    values = np.array([])

    attribute = file.attributes.get(name=attribute_name)
    for attribute_value in attribute.attribute_values.all():
        values = np.append(values, attribute_value.value)

    return values


def get_vector_feature(file):
    vector_feature = np.array([])
    vector_feature = np.append(vector_feature, get_values_of_attribute(file, "Năng lượng trung bình"))
    vector_feature = np.append(vector_feature, get_values_of_attribute(file, "Tốc độ đổi dấu"))
    vector_feature = np.append(vector_feature, get_values_of_attribute(file, "Tỉ lệ khoảng lặng"))
    vector_feature = np.append(vector_feature, get_values_of_attribute(file, "Số lượng tần số"))
    vector_feature = np.append(vector_feature, get_values_of_attribute(file, "Băng thông"))
    return vector_feature


# Tính khoảng cách giữa hai vector (theo Euclid)
def calculate_Euclid_distance(vector1, vector2):
    n = len(vector1)
    result = 0
    for i in range(0, n, 1):
        result = result + (vector1[i] - vector2[i]) ** 2
    return math.sqrt(result)


def calculate(vector_feature_input):
    files = File.objects.all()
    file_result = files[0]
    min_value = -1
    for file in files:
        vector_feature = get_vector_feature(file)
        file.distance = calculate_Euclid_distance(vector_feature_input, vector_feature)
        if min_value == -1:
            min_value = file.distance
        elif min_value > file.distance:
            min_value = file.distance
            file_result = file
    return files, file_result


def extract_vector_features(path, save_folder):
    features = np.array([])

    # Đọc file với tần số lấy mẫu là 44100
    amplitude, _ = librosa.load(path, sr=SAMPLE_RATE)

    # Đặc trưng miền thời gian
    # Năng lượng trung bình
    average_energys = np.array([])
    for i in range(0, len(amplitude), HOP_LENGTH):
        frame = amplitude[i: i + FRAME_SIZE]
        value = average_energy(frame)
        average_energys = np.append(average_energys, value)
        features = np.append(features, value)

    # Tốc độ đổi dấu
    zero_crossing_rates = np.array([])
    for i in range(0, len(amplitude), HOP_LENGTH):
        frame = amplitude[i: i + FRAME_SIZE]
        value = zero_crossing_rate(frame)
        zero_crossing_rates = np.append(zero_crossing_rates, value)
        features = np.append(features, value)

    # Tỉ lệ khoảng lặng
    silence_ratios = np.array([])
    # Ngưỡng biên độ = 5% x biên độ lớn nhất
    amplitude_threshold = 0.05 * np.max(np.abs(amplitude))
    # Ngưỡng thời gian = 0.1% x thời gian của file âm thanh <=> 441 Frame liên tiêp nhau
    time_threshold = 0.001 * len(amplitude)
    for i in range(0, len(amplitude), HOP_LENGTH):
        frame = amplitude[i: i + FRAME_SIZE]
        value = silence_ratio(frame, amplitude_threshold, time_threshold)
        silence_ratios = np.append(silence_ratios, value)
        features = np.append(features, value)

    # Đặc trưng miền tần số
    # Biến đổi dft
    dft_value = dft(amplitude)
    frequencies_range = np.linspace(0, SAMPLE_RATE,
                                    len(dft_value))  # np.linspace(a, b, c): Chia khoảng [a, b] thành c mốc. Mỗi mốc cách nhau (b - a)/(c -1)

    # Do tính chất của phép biến đổi DFT với x(n) là số thục, ta có các giá trị X(k) sẽ bằng X(N-k) với k ≠ 0. Điều này có nghĩa là chúng ta chỉ cần nhìn vào một nửa của kết quả DFT và bỏ thông tin trùng lặp ở nửa kia
    half = (len(dft_value) + 1) // 2
    magnitude_spectrum_range = np.abs(dft_value)[:half]  # Trị tuyệt đối để lấy ra được độ lớn
    frequencies_range = frequencies_range[:half]

    # Các tần số của file
    frequencies, magnitude_spectrum = find_frequencies(frequencies_range, magnitude_spectrum_range)

    # Số lượng tần số
    number_frequencies = len(frequencies)
    features = np.append(features, number_frequencies)

    # Băng thông
    bandwidth = np.max(frequencies) - np.min(frequencies)
    features = np.append(features, bandwidth)

    # Vẽ các biểu đồ
    path_graphs = np.array([])
    total_samples = len(amplitude)
    time_axis = np.linspace(0, total_samples / SAMPLE_RATE, total_samples)
    # Biên độ theo thời gian
    path_graphs = np.append(
        path_graphs,
        draw_graph(time_axis, amplitude, "Thời gian (s)", "Biên độ", "Biên độ theo thời gian", f"{save_folder}/1.png")
    )
    # Biên độ theo tần số
    path_graphs = np.append(path_graphs,
                            draw_graph(frequencies_range, magnitude_spectrum_range, "Tần số (HZ)", "Biên độ",
                                       "Biên độ theo tần số", f"{save_folder}/2.png", 0.3, frequencies,
                                       magnitude_spectrum))
    # Năng lượng trung bình của các frame
    path_graphs = np.append(path_graphs, draw_graph(
        np.arange(0, len(average_energys), 1),
        average_energys,
        "Frame", "Năng lượng trung bình",
        "Năng lượng trung bình của các frame", f"{save_folder}/3.png"
    ))
    # Tốc độ đổi dấu của các frame
    path_graphs = np.append(path_graphs, draw_graph(
        np.arange(0, len(zero_crossing_rates), 1),
        zero_crossing_rates,
        "Frame", "Tốc độ đổi dấu",
        "Tốc độ đổi dấu của các frame", f"{save_folder}/4.png"
    ))
    # Tỉ lệ khoảng lặng
    path_graphs = np.append(path_graphs, draw_graph(
        np.arange(0, len(silence_ratios), 1),
        silence_ratios,
        "Frame", "Tỉ lệ khoảng lặng",
        f"Tỉ lệ khoảng lặng của các frame (ngưỡng thời gian: {time_threshold}, ngưỡng biên độ: {amplitude_threshold})",
        f"{save_folder}/5.png"
    ))
    return features, len(silence_ratios), number_frequencies, bandwidth, path_graphs


def save_file_input(file_input, input_file_label, nhac_cu):
    # Tạo folder lưu file
    join_nhac_cu = "-".join([str(x) for x in nhac_cu])  # Guitar - Piano - Violin
    folder = f'files/{input_file_label}/{join_nhac_cu}'  # files/Hòa tấu/Guitar - Piano - Violin
    folder_len = count_folder(get_real_path(folder))
    folder = f'{folder}/{join_nhac_cu}-{folder_len + 1}'

    # Lưu file
    file_name = f'{input_file_label}-{join_nhac_cu}-{folder_len + 1}.wav'
    _, uploaded_file_url, uploaded_file_path = save_file(f'{folder}/{file_name}', file_input)

    # Trích rút và lưu trữ đặc trưng trưng database
    save_features(file_name, uploaded_file_path, uploaded_file_url, input_file_label, nhac_cu,
                  get_real_folder_path(folder))


def draw_graph(x_axis, y_axis, x_label="", y_label="", title="", absolute_file_path=get_real_path(""), ratio=1,
               frequencies=[], magnitude_spectrum=[]):
    fig, ax = plt.subplots()

    len_max = int(len(x_axis) * ratio)
    x_axis = x_axis[:len_max]
    y_axis = y_axis[:len_max]
    ax.plot(x_axis, y_axis)

    if len(frequencies) > 0 and len(magnitude_spectrum) > 0:
        idx = np.array([np.where(frequencies <= x_axis[len(x_axis) - 1])]).max()
        plt.plot(frequencies[:idx], magnitude_spectrum[:idx], "x")

    ax.set_title(title)
    ax.grid()
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    plt.tight_layout()

    plt.savefig(absolute_file_path, bbox_inches='tight')  # bbox_inches='tight': Bỏ các khoảng trắng thừa có trong ảnh
    plt.cla()
    plt.close(fig)
    return get_relative_path(absolute_file_path)


def export_to_excel(files):
    # Export file excel
    path = get_real_folder_path("files")
    writer = pd.ExcelWriter(f'{path}/Features.xlsx', engine='xlsxwriter')
    column_labels = np.array([
        "#",
        "Tên file",
        "Nhãn",
        "Đường dẫn tương đối",
        "Đường dẫn tuyệt đối"
    ])
    data = np.array([])
    for i, file in enumerate(files):
        data = np.append(data, [i + 1, file.name, file.label, file.relative_path, file.absolute_path])
        for attribute in file.attributes.all():
            attribute_values = attribute.attribute_values.all()
            for j, attribute_value in enumerate(attribute_values):
                column_label = f'{attribute.name}{"" if len(attribute_values) <= 1 else " - (Frame " + str(j) + ")"}'
                if len([label for label in column_labels if label == column_label]) <= 0:
                    column_labels = np.append(column_labels, column_label)
                data = np.append(data, attribute_value.value)

    data = data.reshape(len(files), len(column_labels))
    df = pd.DataFrame(data=data, columns=column_labels)
    df.to_excel(writer, index=False, sheet_name="Features")

    # Điều chỉnh độ rộng của mỗi cột trong excel
    for column in df:
        column_length = max(df[column].astype(str).map(len).max(), len(column))
        col_idx = df.columns.get_loc(column)
        writer.sheets['Features'].set_column(col_idx, col_idx, column_length)

    writer.save()

    return get_real_path(f'{path}/Features.xlsx')


def save_file(path, file):
    fs = FileSystemStorage()
    filename_upload = fs.save(path, file)
    uploaded_file_url = fs.url(filename_upload)  # Đường dẫn render lên giao diện
    uploaded_file_path = fs.path(filename_upload)  # Đường dẫn tuyệt đối
    return filename_upload, uploaded_file_url, uploaded_file_path


def get_real_folder_path(relative_path_folder):
    fs = FileSystemStorage()
    path = fs.path(relative_path_folder)
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as error:
        pass
    return path


def count_folder(path):
    try:
        folder_len = len([name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))])
        return folder_len
    except FileNotFoundError:
        folder_len = 0
        return folder_len


def delete_file(file_absolute_path, delete_parent_folder=True):
    try:
        if delete_parent_folder is False:
            os.remove(file_absolute_path)
        else:
            path = Path(file_absolute_path)

            # Xóa thư mục chứa file
            shutil.rmtree(path.parent.absolute())

            # Nếu thư mục cha chứa nó cx rỗng thì xóa nốt
            path = Path(path.parent.absolute())
            os.removedirs(path.parent.absolute())
    except:
        pass


def save_features(file_name, file_absolute_path, file_relative_path, label, nhac_cu, save_folder):
    # Đọc file với tần số lấy mẫu là 44100
    amplitude, _ = librosa.load(file_absolute_path, sr=SAMPLE_RATE)
    try:
        with transaction.atomic():
            file = File.objects.create(
                name=file_name,
                absolute_path=file_absolute_path,
                relative_path=file_relative_path,
                label=label
            )

            for value in nhac_cu:
                MusicalInstrument.objects.create(
                    file=file,
                    name=value
                )

            # Trich rút đặc trưng

            # Đặc trưng miền thời gian
            # Năng lượng trung bình
            average_energy_attribute = Attribute.objects.create(
                file=file,
                name="Năng lượng trung bình"
            )
            for i in range(0, len(amplitude), HOP_LENGTH):
                frame = amplitude[i: i + FRAME_SIZE]
                AttributeValue.objects.create(
                    attribute=average_energy_attribute,
                    value=average_energy(frame)
                )
            # Tốc độ đổi dấu
            zero_crossing_rate_attribute = Attribute.objects.create(
                file=file,
                name="Tốc độ đổi dấu"
            )
            for i in range(0, len(amplitude), HOP_LENGTH):
                frame = amplitude[i: i + FRAME_SIZE]
                AttributeValue.objects.create(
                    attribute=zero_crossing_rate_attribute,
                    value=zero_crossing_rate(frame)
                )
            # Tỉ lệ khoảng lặng
            silence_ratio_attribute = Attribute.objects.create(
                file=file,
                name="Tỉ lệ khoảng lặng"
            )
            # Ngưỡng biên độ = 5% x biên độ lớn nhất
            amplitude_threshold = 0.05 * np.max(np.abs(amplitude))
            # Ngưỡng thời gian = 0.1% x thời gian của file âm thanh
            time_threshold = 0.001 * len(amplitude)
            for i in range(0, len(amplitude), HOP_LENGTH):
                frame = amplitude[i: i + FRAME_SIZE]
                AttributeValue.objects.create(
                    attribute=silence_ratio_attribute,
                    value=silence_ratio(frame, amplitude_threshold, time_threshold)
                )

            # Đặc trưng miền tần số
            # Biến đổi dft
            dft_value = dft(amplitude)
            frequencies_range = np.linspace(0, SAMPLE_RATE,
                                            len(dft_value))  # np.linspace(a, b, c): Chia khoảng [a, b] thành c mốc. Mỗi mốc cách nhau (b - a)/(c -1)

            # Do tính chất của phép biến đổi DFT với x(n) là số thục, ta có các giá trị X(k) sẽ bằng X(N-k) với k ≠ 0. Điều này có nghĩa là chúng ta chỉ cần nhìn vào một nửa của kết quả DFT và bỏ thông tin trùng lặp ở nửa kia
            half = (len(dft_value) + 1) // 2
            magnitude_spectrum_range = np.abs(dft_value)[:half]  # Trị tuyệt đối để lấy ra được độ lớn
            frequencies_range = frequencies_range[:half]

            # Các tần số của file
            frequencies, magnitude_spectrum = find_frequencies(frequencies_range, magnitude_spectrum_range)

            # Số lượng tần số
            number_frequencies_attribute = Attribute.objects.create(
                file=file,
                name="Số lượng tần số"
            )
            AttributeValue.objects.create(
                attribute=number_frequencies_attribute,
                value=len(frequencies)
            )

            # Băng thông
            bandwidth_attribute = Attribute.objects.create(
                file=file,
                name="Băng thông"
            )
            AttributeValue.objects.create(
                attribute=bandwidth_attribute,
                value=np.max(frequencies) - np.min(frequencies)
            )

            # Vẽ các biểu đồ
            total_samples = len(amplitude)
            time_axis = np.linspace(0, total_samples / SAMPLE_RATE, total_samples)
            # Biên độ theo thời gian
            Chart.objects.create(
                file=file,
                name="Biên độ theo thời gian",
                absolute_path=f"{save_folder}/1.png",
                relative_path=draw_graph(time_axis, amplitude, "Thời gian (s)", "Biên độ", "Biên độ theo thời gian",
                                         f"{save_folder}/1.png")
            )
            # Biên độ theo tần số
            Chart.objects.create(
                file=file,
                name="Biên độ theo tần số",
                absolute_path=f"{save_folder}/2.png",
                relative_path=draw_graph(frequencies_range, magnitude_spectrum_range, "Tần số (HZ)", "Biên độ",
                                         "Biên độ theo tần số", f"{save_folder}/2.png", 0.3, frequencies,
                                         magnitude_spectrum)
            )
            # Năng lượng trung bình của các frame
            attribute_values = AttributeValue.objects.filter(attribute=average_energy_attribute).all()
            Chart.objects.create(
                file=file,
                name="Năng lượng trung bình của các frame",
                absolute_path=f"{save_folder}/3.png",
                relative_path=draw_graph(
                    np.arange(0, len(attribute_values), 1),
                    [attribute_value.value for attribute_value in attribute_values],
                    "Frame", "Năng lượng trung bình",
                    "Năng lượng trung bình của các frame", f"{save_folder}/3.png"
                )
            )
            # Tốc độ đổi dấu của các frame
            attribute_values = AttributeValue.objects.filter(attribute=zero_crossing_rate_attribute).all()
            Chart.objects.create(
                file=file,
                name="Tốc độ đổi dấu của các frame",
                absolute_path=f"{save_folder}/4.png",
                relative_path=draw_graph(
                    np.arange(0, len(attribute_values), 1),
                    [attribute_value.value for attribute_value in attribute_values],
                    "Frame", "Tốc độ đổi dấu",
                    "Tốc độ đổi dấu của các frame", f"{save_folder}/4.png"
                )
            )
            # Tỉ lệ khoảng lặng
            attribute_values = AttributeValue.objects.filter(attribute=silence_ratio_attribute).all()
            Chart.objects.create(
                file=file,
                name="Tỉ lệ khoảng lặng của các frame",
                absolute_path=f"{save_folder}/5.png",
                relative_path=draw_graph(
                    np.arange(0, len(attribute_values), 1),
                    [attribute_value.value for attribute_value in attribute_values],
                    "Frame", "Tỉ lệ khoảng lặng",
                    f"Tỉ lệ khoảng lặng của các frame (ngưỡng thời gian: {time_threshold}, ngưỡng biên độ: {amplitude_threshold})",
                    f"{save_folder}/5.png"
                )
            )
    except:
        traceback.print_exc()
