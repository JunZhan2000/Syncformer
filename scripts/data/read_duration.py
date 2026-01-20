import os
import argparse
import json
from multiprocessing import Pool, cpu_count
from functools import partial
from tqdm import tqdm
import torchvision.io


def get_video_info(vid_path):
    """读取单个视频信息"""
    try:
        video, audio, info = torchvision.io.read_video(vid_path, pts_unit='sec')
        
        # 视频信息
        video_frames = video.shape[0]
        video_height = video.shape[1]
        video_width = video.shape[2]
        video_fps = info.get('video_fps', None)
        video_duration = video_frames / video_fps if video_fps else None
        
        # 音频信息
        if audio.numel() > 0:
            audio_samples = audio.shape[1]
            audio_sample_rate = info.get('audio_fps', None)
            audio_duration = audio_samples / audio_sample_rate if audio_sample_rate else None
        else:
            audio_samples = 0
            audio_sample_rate = None
            audio_duration = None
        
        return {
            'path': vid_path,
            'filename': os.path.basename(vid_path),
            'video_duration': video_duration,
            'video_fps': video_fps,
            'video_frames': video_frames,
            'video_resolution': f"{video_width}x{video_height}",
            'audio_duration': audio_duration,
            'audio_sample_rate': audio_sample_rate,
            'audio_samples': audio_samples,
            'error': None
        }
    except Exception as e:
        return {
            'path': vid_path,
            'filename': os.path.basename(vid_path),
            'video_duration': None,
            'video_fps': None,
            'video_frames': None,
            'video_resolution': None,
            'audio_duration': None,
            'audio_sample_rate': None,
            'audio_samples': None,
            'error': str(e)
        }


def process_videos(folder, num_workers=None):
    """多进程处理所有视频"""
    if num_workers is None:
        num_workers = max(1, cpu_count() - 1)
    
    # 获取所有mp4文件
    mp4_files = []
    for root, dirs, files in os.walk(folder):
        for f in files:
            if f.lower().endswith('.mp4'):
                mp4_files.append(os.path.join(root, f))
    
    mp4_files.sort()
    print(f"找到 {len(mp4_files)} 个MP4文件，使用 {num_workers} 个进程处理...\n")
    
    results = []
    with Pool(num_workers) as pool:
        for result in tqdm(pool.imap(get_video_info, mp4_files), total=len(mp4_files), desc="处理视频"):
            results.append(result)
    
    return results


def save_results(results, output_path):
    """保存结果到JSON文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到: {output_path}")


def load_results(input_path):
    """从JSON文件加载结果"""
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def filter_by_duration(results, threshold, media_type='video', comparison='less'):
    """根据时长筛选"""
    filtered = []
    duration_key = f'{media_type}_duration'
    
    for r in results:
        duration = r.get(duration_key)
        if duration is None:
            continue
        
        if comparison == 'less' and duration < threshold:
            filtered.append(r)
        elif comparison == 'greater' and duration > threshold:
            filtered.append(r)
        elif comparison == 'equal' and abs(duration - threshold) < 0.01:
            filtered.append(r)
    
    return filtered


def print_statistics(results):
    """打印统计信息"""
    total = len(results)
    errors = sum(1 for r in results if r['error'])
    valid_video = [r for r in results if r['video_duration'] is not None]
    valid_audio = [r for r in results if r['audio_duration'] is not None]
    
    print("\n" + "=" * 60)
    print("统计信息")
    print("=" * 60)
    print(f"总文件数: {total}")
    print(f"读取失败: {errors}")
    print(f"有效视频: {len(valid_video)}")
    print(f"有效音频: {len(valid_audio)}")
    
    if valid_video:
        durations = [r['video_duration'] for r in valid_video]
        print(f"\n视频时长统计:")
        print(f"  最短: {min(durations):.2f} 秒")
        print(f"  最长: {max(durations):.2f} 秒")
        print(f"  平均: {sum(durations)/len(durations):.2f} 秒")
    
    if valid_audio:
        durations = [r['audio_duration'] for r in valid_audio]
        print(f"\n音频时长统计:")
        print(f"  最短: {min(durations):.2f} 秒")
        print(f"  最长: {max(durations):.2f} 秒")
        print(f"  平均: {sum(durations)/len(durations):.2f} 秒")
    
    print("=" * 60)


def interactive_mode(results):
    """交互式查询模式"""
    print("\n" + "=" * 60)
    print("进入交互式查询模式")
    print("=" * 60)
    
    help_text = """
命令格式:
  video < N    - 显示视频时长小于N秒的文件
  video > N    - 显示视频时长大于N秒的文件
  audio < N    - 显示音频时长小于N秒的文件
  audio > N    - 显示音频时长大于N秒的文件
  stats        - 显示统计信息
  help         - 显示帮助
  quit/exit/q  - 退出

示例:
  video < 5    - 显示视频时长小于5秒的文件
  audio < 10   - 显示音频时长小于10秒的文件
"""
    print(help_text)
    
    while True:
        try:
            cmd = input("\n>>> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n退出")
            break
        
        if not cmd:
            continue
        
        if cmd in ['quit', 'exit', 'q']:
            print("退出")
            break
        
        if cmd == 'help':
            print(help_text)
            continue
        
        if cmd == 'stats':
            print_statistics(results)
            continue
        
        # 解析查询命令
        parts = cmd.split()
        if len(parts) != 3:
            print("无效命令，输入 help 查看帮助")
            continue
        
        media_type, op, threshold_str = parts
        
        if media_type not in ['video', 'audio']:
            print("媒体类型必须是 video 或 audio")
            continue
        
        if op not in ['<', '>']:
            print("比较符必须是 < 或 >")
            continue
        
        try:
            threshold = float(threshold_str)
        except ValueError:
            print("阈值必须是数字")
            continue
        
        comparison = 'less' if op == '<' else 'greater'
        filtered = filter_by_duration(results, threshold, media_type, comparison)
        
        print(f"\n找到 {len(filtered)} 个文件（{media_type}时长 {op} {threshold}秒）:")
        print("-" * 60)
        
        if filtered:
            # 按时长排序
            duration_key = f'{media_type}_duration'
            filtered.sort(key=lambda x: x[duration_key] or 0)
            
            # 显示结果
            for i, r in enumerate(filtered, 1):
                duration = r[duration_key]
                print(f"{i:4d}. [{duration:8.2f}s] {r['path']}")
            
            # 询问是否保存
            print("-" * 60)
            save_cmd = input("是否保存文件列表? (输入文件名保存，回车跳过): ").strip()
            if save_cmd:
                try:
                    with open(save_cmd, 'w', encoding='utf-8') as f:
                        for r in filtered:
                            f.write(f"{r['path']}\n")
                    print(f"已保存到: {save_cmd}")
                except Exception as e:
                    print(f"保存失败: {e}")
        else:
            print("没有符合条件的文件")


def main():
    parser = argparse.ArgumentParser(description='读取MP4视频信息')
    parser.add_argument('folder', type=str, nargs='?', help='包含MP4文件的文件夹路径')
    parser.add_argument('--output', '-o', type=str, default='video_info.json', help='输出JSON文件路径')
    parser.add_argument('--load', '-l', type=str, help='从已有JSON文件加载结果')
    parser.add_argument('--workers', '-w', type=int, default=None, help='进程数')
    args = parser.parse_args()
    
    if args.load:
        # 从文件加载
        print(f"从文件加载结果: {args.load}")
        results = load_results(args.load)
        print(f"加载了 {len(results)} 条记录")
    elif args.folder:
        # 处理视频文件夹
        results = process_videos(args.folder, args.workers)
        save_results(results, args.output)
    else:
        parser.print_help()
        return
    
    # 打印统计信息
    print_statistics(results)
    
    # 进入交互模式
    interactive_mode(results)


if __name__ == '__main__':
    main()