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

def train_process(file_path):
    os.chdir(os.path.dirname(__file__))

    # Cuda setting
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    # configure loading
    args = utils.load_config('./configs/sins.yaml')

    # set path
    MP4_DATA_PATH   = 'preprocess/mp4'
    ORIGINAL_PATH   = 'preprocess/original/'
    DEMUCS_PATH     = 'preprocess/demucs/'
    NORM_PATH       = 'preprocess/norm/'
    TEMP_LOG_PATH   = 'temp_ffmpeg_log.txt'  # ffmpeg의 무음 감지 로그의 임시 저장 위치

    shutil.copy(file_path, ORIGINAL_PATH + 'sample.wav')
    print(f"{file_path}가 {ORIGINAL_PATH}에 복사되었습니다.")

    demucs(ORIGINAL_PATH, DEMUCS_PATH)

    for filepath in tqdm(glob(DEMUCS_PATH+"*.wav"), desc="노멀라이징 작업 중..."):
        filename = os.path.splitext(os.path.basename(filepath))[0]
        out_filepath = os.path.join(NORM_PATH, filename) + ".wav"
        audio_norm(filepath, out_filepath, sample_rate = 44100)

    for filepath in tqdm(glob(NORM_PATH+"*.wav"), desc="음원 자르는 중..."):
        duration = librosa.get_duration(filename=filepath)
        max_last_seg_duration = 0
        sep_duration_final = 15
        sep_duration = 15

        while sep_duration > 4:
            last_seg_duration = duration % sep_duration
            if max_last_seg_duration < last_seg_duration:
                max_last_seg_duration = last_seg_duration
                sep_duration_final = sep_duration
            sep_duration -= 1
    
        filename = os.path.splitext(os.path.basename(filepath))[0]
        out_filepath = os.path.join(args.data.train_path,"audio", f"{filename}-%04d.wav")
        subprocess.run(f'ffmpeg -i "{filepath}" -f segment -segment_time {sep_duration_final} "{out_filepath}" -y', capture_output=True, shell=True)

    for filepath in tqdm(glob(args.data.train_path+"/audio/*.wav"), desc="무음 제거 중..."):
        if os.path.exists(TEMP_LOG_PATH):
            os.remove(TEMP_LOG_PATH)

        ffmpeg_arg = get_ffmpeg_args(filepath)
        subprocess.run(ffmpeg_arg, capture_output=True, shell=True)

        start = None
        end = None

        with open(TEMP_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f.readlines():
                line = line.strip()
                if "lavfi.silence_start" in line:
                    start = float(line.split("=")[1])
                if "lavfi.silence_end" in line:
                    end = float(line.split("=")[1])

        if start != None:
            if start == 0 and end == None:
                os.remove(filepath)
                
    if os.path.exists(TEMP_LOG_PATH):
            os.remove(TEMP_LOG_PATH)

    main()

    # get data
    sample_rate = args.data.sampling_rate
    hop_size = args.data.block_size

    # initialize f0 extractor
    f0_extractor = F0_Extractor(
                        args.data.f0_extractor, 
                        args.data.sampling_rate, 
                        args.data.block_size, 
                        args.data.f0_min, 
                        args.data.f0_max)

    # initialize volume extractor
    volume_extractor = Volume_Extractor(args.data.block_size)

    # initialize mel extractor
    mel_extractor = None
    if args.model.type == 'Diffusion':
        mel_extractor = Vocoder(args.vocoder.type, args.vocoder.ckpt, device = device)
        if mel_extractor.vocoder_sample_rate != sample_rate or mel_extractor.vocoder_hop_size != hop_size:
            mel_extractor = None
            print('Unmatch vocoder parameters, mel extraction is ignored!')

    # initialize units encoder
    if args.data.encoder == 'cnhubertsoftfish':
        cnhubertsoft_gate = args.data.cnhubertsoft_gate
    else:
        cnhubertsoft_gate = 10             
    units_encoder = Units_Encoder(
                        args.data.encoder, 
                        args.data.encoder_ckpt, 
                        args.data.encoder_sample_rate, 
                        args.data.encoder_hop_size, 
                        device = device)    

    # preprocess training set
    preprocess(args.data.train_path, f0_extractor, volume_extractor, mel_extractor, units_encoder, sample_rate, hop_size, device = device)

    # preprocess validation set
    preprocess(args.data.valid_path, f0_extractor, volume_extractor, mel_extractor, units_encoder, sample_rate, hop_size, device = device)

    print("**** train start SUCCESS ****")
    ddsp_train(args)
