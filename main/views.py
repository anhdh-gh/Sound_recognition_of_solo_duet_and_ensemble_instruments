import os
import shutil
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View

from Sound_recognition_of_solo_duet_and_ensemble_instruments import settings
from main.models import File, MusicalInstrument
from main.util import save_file, count_folder, get_real_path, save_features, export_to_excel, delete_file, \
    get_relative_path, get_real_folder_path


class HomeHandler(View):
    def get(self, request):
        return render(request, "home.html", {'result': False})

    def post(self, request):
        # Lấy file gửi lên và lưu file
        file_input = request.FILES['file-input']
        _, uploaded_file_url, _ = save_file(f'file-input/{file_input.name}', file_input)

        # Xử lý

        # Trả về kết quả
        return render(request, "home.html", {
            'uploaded_file_url': uploaded_file_url,
            'result': True,
            'file_name': file_input.name
        })


class DashboardHandler(View):
    def get(self, request):
        files = File.objects.all()

        # Hiển thị giao diện
        return render(request, "dashboard.html", {"files": files})


class DashboardAddFiledHandler(View):
    def get(self, request):
        return render(request, "add-file.html", {})

    def post(self, request):
        # Lấy file gửi lên
        file_input = request.FILES['file-input']
        input_file_label = request.POST.get('input-file-label')
        nhac_cu = request.POST.getlist('nhac_cu')

        # Tạo folder lưu file
        join_nhac_cu = " - ".join([str(x) for x in nhac_cu])  # Guitar - Piano - Violin
        folder = f'files/{input_file_label}/{join_nhac_cu}'  # files/Hòa tấu/Guitar - Piano - Violin
        folder_len = count_folder(get_real_path(folder))
        folder = f'{folder}/{join_nhac_cu} - {folder_len + 1}'

        # Lưu file
        file_name = f'{input_file_label} - {join_nhac_cu} - {folder_len + 1}.wav'
        _, uploaded_file_url, uploaded_file_path = save_file(f'{folder}/{file_name}', file_input)

        # Trích rút và lưu trữ đặc trưng trưng database
        save_features(file_name, uploaded_file_path, uploaded_file_url, input_file_label, nhac_cu)

        # Trả về kết quả
        return redirect(reverse('main:dashboard'))


class DashboardEditFiledHandler(View):
    def get(self, request, id):
        file = File.objects.get(pk=id)
        return render(request, "edit-file.html", {"file": file})

    def post(self, request, id):
        try:
            with transaction.atomic():
                file = File.objects.get(pk=id)
                file.label = request.POST.get('input-file-label')
                nhac_cu = request.POST.getlist('nhac_cu')

                # Copy file cũ sang một thư mục khác
                tempt_folder_path = get_real_folder_path(f'tempt')
                shutil.copyfile(file.absolute_path, f'{tempt_folder_path}/{file.name}')

                # Xóa file cũ trong thư mục media
                delete_file(file.absolute_path)

                # Tạo folder lưu file
                join_nhac_cu = " - ".join([str(x) for x in nhac_cu])  # Guitar - Piano - Violin
                folder = f'files/{file.label}/{join_nhac_cu}'  # files/Hòa tấu/Guitar - Piano - Violin
                folder_len = count_folder(get_real_path(folder))
                folder = f'{folder}/{join_nhac_cu} - {folder_len + 1}'

                # Lưu file
                file_name = f'{file.label} - {join_nhac_cu} - {folder_len + 1}.wav'
                shutil.copyfile(f'{tempt_folder_path}/{file.name}', get_real_folder_path(f'{folder}') + f'/{file_name}')

                ## Xóa file trong thư mục tempt
                delete_file(f'{tempt_folder_path}/{file.name}', delete_parent_folder=False)
                file.name = file_name

                # Chỉnh sửa lại đường dẫn
                file.relative_path = get_relative_path(f'{folder}/{file_name}')
                file.absolute_path = get_real_path(f'{folder}/{file_name}')

                # Chỉnh sửa lại nhạc cụ
                file.musical_instruments.all().delete()
                for value in nhac_cu:
                    MusicalInstrument.objects.create(
                        file=file,
                        name=value
                    )
                file.save()
        except:
            traceback.print_exc()
        return redirect(reverse('main:dashboard'))


class DashboardDeleteFiledHandler(View):
    def get(self, request, id):
        # Xóa file trong database
        file = File.objects.get(pk=id)
        file.delete()

        # Xóa file trong thư mục media
        delete_file(file.absolute_path)

        return redirect(reverse('main:dashboard'))


class DownloadFeaturesExcelHandler(View):
    def get(self, request):
        # Thực hiện export to excel
        export_to_excel(File.objects.all())
        file_path = export_to_excel(File.objects.all())
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                return response
        raise Http404
