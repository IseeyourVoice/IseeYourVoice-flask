import os
import shutil
import librosa
import torch
from DDSP_SVC_KOR_master.logger import utils
from tqdm import tqdm
from glob import glob
from pydub import AudioSegment
from DDSP_SVC_KOR_master.logger.utils import traverse_dir
from DDSP_SVC_KOR_master.sep_wav import demucs
from DDSP_SVC_KOR_master.sep_wav import audio_norm
import subprocess
from DDSP_SVC_KOR_master.sep_wav import get_ffmpeg_args
from DDSP_SVC_KOR_master.draw import main
from DDSP_SVC_KOR_master.preprocess import preprocess
from DDSP_SVC_KOR_master.ddsp.vocoder import F0_Extractor, Volume_Extractor, Units_Encoder
from DDSP_SVC_KOR_master.diffusion.vocoder import Vocoder
from DDSP_SVC_KOR_master.train import ddsp_train
from types import SimpleNamespace
from DDSP_SVC_KOR_master.main import inference
from mail.mail import mail, send_mail, send_training_complete_email, send_inference_complete_email
from datetime import datetime
from flask import session
import yaml
from pathlib import Path

def make_process(file_path, file_name, model_path, model_name):
    os.chdir(os.path.dirname(__file__))

    INPUT_PATH = "output/input/"
    MODEL_PATH = str(model_path)
    OUTPUT_PATH = 'output/result/'

    config_path = os.path.join(os.path.dirname(model_path), 'config.yaml')
    if not os.path.exists(config_path):
        # config.yaml 파일 생성 내용
        config_content = {
            'data': {
                'block_size': 512,
                'cnhubertsoft_gate': 10,
                'duration': 2,
                'encoder': 'hubertsoft',
                'encoder_ckpt': 'pretrain/hubert/hubert-soft-0d54a1f4.pt',
                'encoder_hop_size': 320,
                'encoder_out_channels': 256,
                'encoder_sample_rate': 16000,
                'f0_extractor': 'parselmouth',
                'f0_max': 800,
                'f0_min': 65,
                'sampling_rate': 44100,
                'train_path': 'data/train',
                'valid_path': 'data/val',
            },
            'device': 'cuda',
            'enhancer': {
                'ckpt': 'pretrain/nsf_hifigan/model',
                'type': 'nsf-hifigan',
            },
            'env': {
                'expdir': 'exp/sins-test',
                'gpu_id': 0,
            },
            'loss': {
                'fft_max': 2048,
                'fft_min': 256,
                'n_scale': 4,
            },
            'model': {
                'n_harmonics': 128,
                'n_mag_allpass': 256,
                'n_mag_noise': 256,
                'n_spk': 1,
                'type': 'Sins',
            },
            'train': {
                'batch_size': 24,
                'cache_all_data': True,
                'cache_device': 'cpu',
                'cache_fp16': True,
                'epochs': 100000,
                'interval_log': 10,
                'interval_val': 2000,
                'lr': 0.0005,
                'num_workers': 2,
                'save_opt': False,
                'weight_decay': 0,
            }
        }

        # config.yaml 파일 생성
        with open(config_path, 'w') as file:
            yaml.dump(config_content, file, default_flow_style=False, allow_unicode=True)

        print(f"{config_path} 파일이 생성되었습니다.")
    else:
        print(f"{config_path} 파일이 이미 존재합니다.")

    shutil.copy(file_path, INPUT_PATH + str(file_name))
    print(f"{file_path}가 {OUTPUT_PATH}'에 복사되었습니다.")

    # configure setting
    configures = {
        'model_path'            :   MODEL_PATH, # 추론에 사용하고자 하는 모델
        'input'                 :   INPUT_PATH + str(file_name), # 추론하고자 하는 노래파일의 위치
        'output'                :   OUTPUT_PATH + str(file_name), # 결과물 파일의 위치
        'device'                :   'cuda',
        'spk_id'                :   '1', 
        'spk_mix_dict'          :   'None', 
        'key'                   :   '0', 
        'enhance'               :   'true' , 
        'pitch_extractor'       :   'crepe' ,
        'f0_min'                :   '50' ,
        'f0_max'                :   '1100',
        'threhold'              :   '-60',
        'enhancer_adaptive_key' :   '0'
    }
    cmd = SimpleNamespace(**configures)

    # 추론 시작
    print("**** make start SUCCESS ****")
    inference(cmd)

    # 추론 완료 음성 계정 이전
    now = datetime.now()
    formatted_now = now.strftime("%Y%m%d_%H%M%S")

    final_cover_path = OUTPUT_PATH + str(file_name)

    user_id = session.get('user', {}).get('id')
    if user_id:
        account_local_path = f'../account/{user_id}/cover/'

    if not os.path.exists(Path(account_local_path)):
        os.makedirs(Path(account_local_path))

    if Path(final_cover_path).exists():
        shutil.copy(Path(final_cover_path), Path(account_local_path + f'{formatted_now}_{str(file_name)}'))

    # 추론 완료 메일 발송
    print("**** make finish SUCCESS ****")
    # send_inference_complete_email()
