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

def make_process(file_path):
    os.chdir(os.path.dirname(__file__))

    shutil.copy(file_path, 'output/' + 'original.wav')
    print(f"{file_path}가 {'output/' + 'original.wav'}에 복사되었습니다.")

    # configure setting
    configures = {
        'model_path'            :   'exp/sins-test/model_2000.pt', # 추론에 사용하고자 하는 모델, 바로위에서 학습한 모델을 가져오면댐
        'input'                 :   'output/original.wav', # 추론하고자 하는 노래파일의 위치 - 님들이 바꿔야댐 
        'output'                :   'output/output.wav',  # 결과물 파일의 위치
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

    print("**** make start SUCCESS ****")
    inference(cmd)
