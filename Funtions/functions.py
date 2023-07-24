import shutil
from datetime import datetime

from yolov5.config import opt, DotDict
from yolov5.functions_for_apis import get_evaluations_in_df
from yolov5.train import main
from database import update
import yaml
from dotenv.main import load_dotenv

import os
import os.path
import requests

import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from scipy.ndimage.filters import gaussian_filter1d
import nvidia_smi
import torch
from database import update_report

load_dotenv()


def create_yaml_file(path_train, path_val, save_path, classes):
    classes = classes.split(',')

    dict_file = {"train": os.path.join(path_train, "images"),
                 "val": os.path.join(path_val, "images"),
                 "names": classes,
                 "nc": len(classes)}

    with open(os.path.join(os.environ["YAML_PATH"], f'{save_path}.yaml'), 'w') as file:
        yaml.dump(dict_file, file)


def train_yolo(items):
    train_data, test_data, pretrained, epoch, batch_size, name, id_train, labels = items
    # try:
    create_yaml_file(path_train=train_data, path_val=test_data, save_path=name, classes=labels)
    new_opt = opt.copy()

    new_opt = DotDict(new_opt)
    new_opt.batch_size = batch_size
    new_opt.name = name
    new_opt.data = os.path.join(os.environ["YAML_PATH"], f'{name}.yaml')
    new_opt.epochs = epoch
    new_opt.weights = pretrained
    new_opt.id_train = id_train
    new_opt.device = os.environ["DEVICE"]
    main(new_opt) 
    update(id_train, "status", 'SUCCESS')
    # requests.get('https://upr-be.gemvietnam.com/amazon-sdk/file',
    #                 body={'id':id_train},
    #                 headers={'x-api-key':os.environ['API_KEYS']})


    # except Exception as e:
    #     update(id_train, "status", 'FAILURE')
    #     print(e)


def plot_results(file='path/to/results.csv', dir='', name=''):
    # Plot training results.csv. Usage: from utils.plots import *; plot_results('path/to/results.csv')
    save_dir = Path(file).parent if file else Path(dir)
    fig, ax = plt.subplots(2, 5, figsize=(12, 6), tight_layout=True)
    ax = ax.ravel()
    files = list(save_dir.glob('results*.csv'))
    assert len(files), f'No results.csv files found in {save_dir.resolve()}, nothing to plot.'
    for f in files:
        try:
            data = pd.read_csv(f)
            s = [x.strip() for x in data.columns]
            x = data.values[:, 0]
            for i, j in enumerate([1, 2, 3, 4, 5, 8, 9, 10, 6, 7]):
                y = data.values[:, j].astype('float')
                # y[y == 0] = np.nan  # don't show zero values
                ax[i].plot(x, y, marker='.', label=f.stem, linewidth=2, markersize=8)  # actual results
                ax[i].plot(x, gaussian_filter1d(y, sigma=3), ':', label='smooth', linewidth=2)  # smoothing line
                ax[i].set_title(s[j], fontsize=12)
                # if j in [8, 9, 10]:  # share train and val loss y axes
                #     ax[i].get_shared_y_axes().join(ax[i], ax[i - 5])
        except Exception as e:
            pass
    ax[1].legend()
    save_path = os.path.join(os.environ['WEIGHTS_PATH'], name)
    print(save_path)
    fig.savefig(os.path.join(save_path, 'results.png'), dpi=200)
    plt.close()


def check_resources(batch_size):
    device = os.environ['DEVICE']

    if 'cuda' in device and torch.cuda.is_available():

        nvidia_smi.nvmlInit()
        handle = nvidia_smi.nvmlDeviceGetHandleByIndex(0)
        info = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
        free_memory = info.free / pow(1024, 3)
        if batch_size * 0.3 + 0.5 <= free_memory:
            return True
        else:
            return False

    elif device == 'cpu':
        return True


def create_total_dataset(name, datasets):
    now_time = str(datetime.now())[:19]
    now = now_time.replace(":", "_")

    dest_dir_images = os.path.join(*[os.environ['PATH_DATA'], name, 'images'])
    if not os.path.exists(dest_dir_images):
        os.makedirs(dest_dir_images)
    dest_dir_annotations = os.path.join(*[os.environ['PATH_DATA'], name, 'annotations'])
    if not os.path.exists(dest_dir_annotations):
        os.makedirs(dest_dir_annotations)

    for data in datasets:
        src_dir = os.path.join(*[os.environ['PATH_DATA'], data])
        files_images = os.listdir(f'{src_dir}/images')
        for file in files_images:
            shutil.copy(os.path.join(*[src_dir, 'images', file]),
                        os.path.join(*[dest_dir_images, f'{str(now)}_{file}']))
        files_labels = os.listdir(f'{src_dir}/annotations')
        for file in files_labels:
            shutil.copy(os.path.join(*[src_dir, 'annotations', file]),
                        os.path.join(*[dest_dir_annotations, f'{str(now)}_{file}']))


def report_model(pretrained_name, datasets,classes,id):

    print( datasets)


    pretrained_path = os.path.join(*[os.environ['WEIGHTS_PATH'],pretrained_name,'weights', 'best.pt'])
    results = {}
    for dataset in datasets:
        dataset_path = os.path.join(os.environ['PATH_DATA'], f'{dataset}/images')
        df, runtime = get_evaluations_in_df(pretrained_path, dataset_path, True,classes)
        results[dataset] = df.to_dict(orient='list')
    update_report(results,id)




