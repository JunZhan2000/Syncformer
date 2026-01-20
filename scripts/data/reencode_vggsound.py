import subprocess
from pathlib import Path
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
from shutil import which as which_ffmpeg
import functools


def reencode_video(path, output_dir, vfps=25, afps=16000, in_size=256):
    """对单个视频进行重编码"""
    try:
        assert which_ffmpeg('ffmpeg') != '', 'Is ffmpeg installed? Check if the conda environment is activated.'
        ffmpeg_path = which_ffmpeg('ffmpeg')
        
        new_path = Path(output_dir) / f'{Path(path).stem}.mp4'
        new_path.parent.mkdir(exist_ok=True, parents=True)
        new_path = str(new_path)
        
        cmd = f'{ffmpeg_path}'
        cmd += ' -hide_banner -loglevel panic'
        cmd += f' -y -i {path}'
        cmd += f" -vf fps={vfps},scale=iw*{in_size}/'min(iw,ih)':ih*{in_size}/'min(iw,ih)',crop='trunc(iw/2)'*2:'trunc(ih/2)'*2"
        cmd += f" -ar {afps}"
        cmd += f' {new_path}'
        subprocess.call(cmd.split())
        
        cmd = f'{ffmpeg_path}'
        cmd += ' -hide_banner -loglevel panic'
        cmd += f' -y -i {new_path}'
        cmd += f' -acodec pcm_s16le -ac 1'
        cmd += f' {new_path.replace(".mp4", ".wav")}'
        subprocess.call(cmd.split())
        
        return (True, Path(path).name, None)
    except Exception as e:
        return (False, Path(path).name, str(e))


def get_slice(files, num_slices, slice_id):
    """将文件列表均分成num_slices份，返回第slice_id份"""
    if slice_id < 0 or slice_id >= num_slices:
        raise ValueError(f"slice_id必须在[0, {num_slices-1}]范围内，当前为{slice_id}")
    
    total = len(files)
    base_size = total // num_slices
    remainder = total % num_slices
    
    # 前remainder个切片多分一个文件
    if slice_id < remainder:
        start = slice_id * (base_size + 1)
        end = start + base_size + 1
    else:
        start = remainder * (base_size + 1) + (slice_id - remainder) * base_size
        end = start + base_size
    
    return files[start:end]


def reencode_folder(input_dir, output_dir, vfps=25, afps=16000, in_size=256, 
                    num_workers=None, num_slices=1, slice_id=0):
    """对文件夹下所有mp4文件进行重编码
    
    Args:
        input_dir: 输入文件夹路径
        output_dir: 输出文件夹路径
        vfps: 视频帧率
        afps: 音频采样率
        in_size: 视频最小边尺寸
        num_workers: 进程数量
        num_slices: 切片总数（将文件均分成多少份）
        slice_id: 当前处理的切片id（从0开始）
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # 获取所有mp4文件并排序（确保每次运行顺序一致）
    all_mp4_files = sorted(list(input_dir.glob('*.mp4')))
    
    if not all_mp4_files:
        print(f"在 {input_dir} 中未找到任何mp4文件")
        return
    
    print(f"总共找到 {len(all_mp4_files)} 个mp4文件")
    
    # 获取当前切片的文件
    mp4_files = get_slice(all_mp4_files, num_slices, slice_id)
    print(f"切片 {slice_id}/{num_slices}: 处理 {len(mp4_files)} 个文件 (索引 {all_mp4_files.index(mp4_files[0]) if mp4_files else 'N/A'} - {all_mp4_files.index(mp4_files[-1]) if mp4_files else 'N/A'})")
    
    if not mp4_files:
        print(f"切片 {slice_id} 没有分配到文件")
        return []
    
    if num_workers is None:
        num_workers = min(cpu_count(), len(mp4_files))
    
    worker_func = functools.partial(
        reencode_video,
        output_dir=output_dir,
        vfps=vfps,
        afps=afps,
        in_size=in_size
    )
    
    failed_files = []
    success_count = 0
    
    with Pool(num_workers) as pool:
        results = list(tqdm(
            pool.imap(worker_func, mp4_files),
            total=len(mp4_files),
            desc=f"重编码视频 (切片 {slice_id}/{num_slices})"
        ))
    
    for success, filename, error in results:
        if success:
            success_count += 1
        else:
            failed_files.append((filename, error))
    
    print(f"\n切片 {slice_id} 处理完成!")
    print(f"成功: {success_count}/{len(mp4_files)}")
    print(f"失败: {len(failed_files)}/{len(mp4_files)}")
    
    if failed_files:
        print("\n失败的文件:")
        for filename, error in failed_files:
            print(f"  - {filename}: {error}")
    
    return failed_files


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='批量重编码视频文件')
    parser.add_argument('--input_dir', type=str, required=True, help='输入文件夹路径')
    parser.add_argument('--output_dir', type=str, required=True, help='输出文件夹路径')
    parser.add_argument('--vfps', type=int, default=25, help='视频帧率')
    parser.add_argument('--afps', type=int, default=16000, help='音频采样率')
    parser.add_argument('--in_size', type=int, default=256, help='视频最小边尺寸')
    parser.add_argument('--num_workers', type=int, default=None, help='进程数量')
    parser.add_argument('--num_slices', type=int, default=1, help='切片总数（将文件均分成多少份）')
    parser.add_argument('--slice_id', type=int, default=0, help='当前处理的切片id（从0开始）')
    
    args = parser.parse_args()
    
    reencode_folder(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        vfps=args.vfps,
        afps=args.afps,
        in_size=args.in_size,
        num_workers=args.num_workers,
        num_slices=args.num_slices,
        slice_id=args.slice_id
    )