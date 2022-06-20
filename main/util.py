import os
import shutil
import traceback
from pathlib import Path

import librosa
import numpy as np
import pandas as pd
from django.core.files.storage import FileSystemStorage
from django.db import transaction

from main.constants import SAMPLE_RATE, HOP_LENGTH, FRAME_SIZE
from main.extract_features import average_energy, zero_crossing_rate, silence_ratio, dft, find_frequencies
from main.models import File, MusicalInstrument, Attribute, AttributeValue


def export_to_excel(files):
    # Export file excel
    fs = FileSystemStorage()
    path = fs.path("files")
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

    return fs.path(f'{path}/Features.xlsx')


def save_file(path, file):
    fs = FileSystemStorage()
    filename_upload = fs.save(path, file)
    uploaded_file_url = fs.url(filename_upload)  # Đường dẫn render lên giao diện
    uploaded_file_path = fs.path(filename_upload)  # Đường dẫn tuyệt đối
    return filename_upload, uploaded_file_url, uploaded_file_path


def get_real_path(relative_path):
    fs = FileSystemStorage()
    path = fs.path(relative_path)
    return path


def get_real_folder_path(relative_path_folder):
    fs = FileSystemStorage()
    path = fs.path(relative_path_folder)
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as error:
        pass
    return path


def get_relative_path(real_path):
    fs = FileSystemStorage()
    return fs.url(real_path)


def count_folder(path):
    try:
        folder_len = len([name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))])
        return folder_len
    except FileNotFoundError:
        folder_len = 0
        return folder_len


def delete_file(file_absolute_path, delete_parent_folder=True):
    if delete_parent_folder is False:
        os.remove(file_absolute_path)
    else:
        path = Path(file_absolute_path)

        # Xóa thư mục chứa file
        shutil.rmtree(path.parent.absolute())
        try:
            # Nếu thư mục cha chứa nó cx rỗng thì xóa nốt
            path = Path(path.parent.absolute())
            os.removedirs(path.parent.absolute())
        except:
            traceback.print_exc()


def save_features(file_name, file_absolute_path, file_relative_path, label, nhac_cu):
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
            # tỉ lệ khoảng lặng
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
            # Giải tần số
            frequencies = find_frequencies(dft_value)

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
    except:
        traceback.print_exc()
