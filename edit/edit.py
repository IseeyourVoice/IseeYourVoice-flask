import os
from pydub import AudioSegment

def edit_audio(file_name, file_path, start_time, end_time, volume_change, fade_in_time, fade_out_time):
    # 1. 오디오 파일 불러오기
    sound = AudioSegment.from_file(file_path)

    # 2. 오디오 자르기
    sliced_sound = sound[start_time:end_time]

    # 3. 오디오 볼륨 조절
    adjusted_volume = sliced_sound + volume_change  # volume_change는 dB

    # 4. 오디오 페이드 인
    faded_in = adjusted_volume.fade_in(fade_in_time)

    # 5. 오디오 페이드 아웃
    faded_out = faded_in.fade_out(fade_out_time)

    # 6. 저장할 디렉토리 생성
    output_directory = 'uploads/edit/'
    os.makedirs(output_directory, exist_ok=True)

    # 7. 변환된 사운드 파일 저장
    output_file_path = os.path.join(output_directory, f'{file_name}')
    faded_out.export(output_file_path, format='wav')

    return output_file_path
