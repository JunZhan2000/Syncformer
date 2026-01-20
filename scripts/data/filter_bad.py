import json
import os
import argparse


def load_results(input_path):
    """从JSON文件加载结果"""
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def filter_and_save(results, output_dir='./data/filtered_examples_vggsound_shorter'):
    """筛选并保存bad文件"""
    os.makedirs(output_dir, exist_ok=True)
    
    threshold = 9.5
    
    # 筛选视频时长小于9.5秒的
    video_short = []
    for r in results:
        if r['video_duration'] is not None and r['video_duration'] < threshold:
            filename = os.path.basename(r['path']).replace('.mp4', '')
            video_short.append(filename)
    
    # 筛选音频时长小于9.5秒的
    audio_short = []
    for r in results:
        if r['audio_duration'] is not None and r['audio_duration'] < threshold:
            filename = os.path.basename(r['path']).replace('.mp4', '')
            audio_short.append(filename)
    
    # 筛选读取失败的
    error_files = []
    for r in results:
        if r['error'] is not None:
            filename = os.path.basename(r['path']).replace('.mp4', '')
            error_files.append(filename)
    
    # 保存视频时长过短的文件
    video_short_path = os.path.join(output_dir, 'video_less_than_9.5s.txt')
    with open(video_short_path, 'w', encoding='utf-8') as f:
        for filename in sorted(video_short):
            f.write(f"{filename}\n")
    print(f"视频时长 < {threshold}s: {len(video_short)} 个，已保存到 {video_short_path}")
    
    # 保存音频时长过短的文件
    audio_short_path = os.path.join(output_dir, 'audio_less_than_9.5s.txt')
    with open(audio_short_path, 'w', encoding='utf-8') as f:
        for filename in sorted(audio_short):
            f.write(f"{filename}\n")
    print(f"音频时长 < {threshold}s: {len(audio_short)} 个，已保存到 {audio_short_path}")
    
    # 保存读取失败的文件
    error_path = os.path.join(output_dir, 'read_error.txt')
    with open(error_path, 'w', encoding='utf-8') as f:
        for filename in sorted(error_files):
            f.write(f"{filename}\n")
    print(f"读取失败: {len(error_files)} 个，已保存到 {error_path}")
    
    # 合并所有bad文件（去重）
    all_bad = set(video_short) | set(audio_short) | set(error_files)
    all_bad_path = os.path.join(output_dir, 'all_bad.txt')
    with open(all_bad_path, 'w', encoding='utf-8') as f:
        for filename in sorted(all_bad):
            f.write(f"{filename}\n")
    print(f"所有bad文件（去重）: {len(all_bad)} 个，已保存到 {all_bad_path}")


def main():
    parser = argparse.ArgumentParser(description='根据统计结果生成bad文件列表')
    parser.add_argument('input', type=str, help='之前保存的JSON结果文件路径')
    parser.add_argument('--output-dir', '-o', type=str, 
                        default='./data/filtered_examples_vggsound_shorter',
                        help='输出目录')
    args = parser.parse_args()
    
    print(f"加载结果: {args.input}")
    results = load_results(args.input)
    print(f"共 {len(results)} 条记录")
    
    filter_and_save(results, args.output_dir)


if __name__ == '__main__':
    main()