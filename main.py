import flet as ft

import os

import math

from pathlib import Path

import PIL.Image as Image

from PIL.PngImagePlugin import PngInfo



# グローバル変数の設定

split_counter = 0

split_parts = 0

imgsize = 2000

MB_IMG_DATA = imgsize * imgsize * 3

operation_mode = "None"

filepath = "."

outfolder = Path(filepath).resolve().stem

origname = ""

outputpath = ""

filebytessize = 0



# 与えられたファイルの分割数を推測する関数

def guessSplittedParts(path):

    return math.ceil(Path(path).stat().st_size / MB_IMG_DATA)



# バイト配列から画像を生成する関数

def generateImg(bytearray, size, outfolder_path, orig_filename, filepath):

    global split_counter, split_parts

    outfolder_path = Path(outfolder_path)  # Pathオブジェクトに変換

    if not outfolder_path.exists():  # .exists() メソッドをPathオブジェクトに対して使用

        os.makedirs(outfolder_path)

    # 元のファイル名とサイズを画像のメタデータに追加

    filename, file_extension = os.path.splitext(filepath)

    infinidata = PngInfo()

    infinidata.add_text("OrigName", f'{filename}{file_extension}')

    file_stats = os.stat(filepath)

    infinidata.add_text("OrigSize", f'{file_stats.st_size}')

    # バイト配列から画像を作成して保存

    img = Image.frombytes("RGB", (size, size), bytes(bytearray))

    img_name = f'{orig_filename}_{str(split_counter).zfill(len(str(guessSplittedParts(filepath))))}.png'

    img_path = os.path.join(outfolder_path, img_name)

    img.save(img_path, "PNG", pnginfo=infinidata)

    split_counter += 1



# バイナリデータから画像を生成して保存する関数

def openFileBinary(path, outfolder, orig_filename, imgsize):

    global split_parts, MB_IMG_DATA

    with open(path, "rb") as bf:

        raw_data = bytearray()

        while (byte := bf.read(1)):

            raw_data += byte

            # 定義されたサイズに達したら画像を生成

            if len(raw_data) == MB_IMG_DATA:

                generateImg(raw_data, imgsize, outfolder, orig_filename, path)

                raw_data.clear()

        # 残りのデータを画像として保存

        raw_data += bytearray(bytes(MB_IMG_DATA - len(raw_data)))

        generateImg(raw_data, imgsize, outfolder, orig_filename, path)



# 分割された画像を元のファイルに結合する関数

def mergeImages(path, outputpath):

    global MB_IMG_DATA, origname

    file_list = os.listdir(path)

    file_list.sort()

    # 最初の画像ファイルを開き、メタデータから元のファイル名とサイズを取得

    im = Image.open(os.path.join(path, file_list[0]), mode='r')

    orig_name = im.text.get('OrigName')

    orig_size = int(im.text.get('OrigSize'))

    # 出力用のディレクトリを作成

    if not os.path.exists(outputpath):

        os.makedirs(outputpath)

    # 出力ファイルのパスを生成（パスはユーザの指定に従い、名前と形式はメタデータから取得）

    outputfile_path = os.path.join(outputpath, Path(orig_name).name)

    # 既にファイルが存在する場合は削除

    if os.path.isfile(outputfile_path):

        os.remove(outputfile_path)

    # マージしたデータを書き込むファイルを開く

    with open(outputfile_path, "ab") as recovered:

        for file in file_list:

            im = Image.open(os.path.join(path, file), mode='r')

            im_width, im_height = im.size

            MB_IMG_DATA = im_width * im_height * 3

            # すべてのピクセルデータをバイト配列に変換

            pixel_list = bytearray([pixel for pixel_tuple in list(im.getdata()) for pixel in pixel_tuple])

            # 最後の画像には不要なパディングを削除

            if file == file_list[-1]:

                bytestopad = (len(file_list) * MB_IMG_DATA) - orig_size

                pixel_list = pixel_list[:-(bytestopad)]

            # ピクセルデータを書き込み

            recovered.write(pixel_list)



# FletのUIを設定

def main(page: ft.Page):

    page.title = "File to Image Encoder/Decoder"

    page.update()



    def on_split(e):

        global split_parts, filepath, outfolder, imgsize, MB_IMG_DATA



        directory = file_to_split.value

        output_folder = output_folder_split.value or f"{Path(directory).stem}_split"

        imgsize = int(image_size.value)

        MB_IMG_DATA = imgsize * imgsize * 3



        if os.path.isdir(directory):

            for filename in os.listdir(directory):

                filepath = Path(directory) / filename

                if os.path.isfile(filepath):

                    orig_filename = Path(filepath).stem

                    file_outfolder = Path(output_folder) / f"{orig_filename}_split"

                    split_parts = guessSplittedParts(filepath)

                    openFileBinary(filepath, file_outfolder, orig_filename, imgsize)

            result.value = "The files have been split into images."

        else:

            result.value = "A directory with that name does not exist."



        page.update()



    def on_merge(e):

        global outfolder, outputpath

        outfolder = folder_to_merge.value

        outputpath = merged_output_folder.value or f"{outfolder}_merged"

        if os.path.exists(outfolder):

            mergeImages(outfolder, outputpath)

            result.value = f"The file has been recovered as '{outputpath}'"

        else:

            result.value = "Can't find folder with that name."

        page.update()



    # UI要素の作成

    file_to_split = ft.TextField(label="Folder to split", width=300)

    output_folder_split = ft.TextField(label="Output folder (optional)", width=300)

    image_size = ft.TextField(label="Image size", value=str(imgsize), width=100)

    split_button = ft.ElevatedButton("Split", on_click=on_split)

    folder_to_merge = ft.TextField(label="Folder to merge", width=300)

    merged_output_folder = ft.TextField(label="Merged output folder (optional)", width=300)

    merge_button = ft.ElevatedButton("Merge", on_click=on_merge)

    result = ft.Text()



    # UIのレイアウト設定

    page.add(

        ft.Column([

            ft.Text("Split files in a folder into images"),

            file_to_split,

            output_folder_split,

            image_size,

            split_button,

            ft.Divider(),

            ft.Text("Merge images into a file"),

            folder_to_merge,

            merged_output_folder,

            merge_button,

            ft.Divider(),

            result,

        ])

    )



# アプリケーションのメイン関数を設定

ft.app(target=main)
