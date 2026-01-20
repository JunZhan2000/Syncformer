import csv
import os
import shutil
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import argparse


def process_file(args):
    """检查单个文件是否存在，如果存在则复制到目标文件夹"""
    name, id_str, folder_path, output_folder = args
    # 将id填充到6位
    padded_id = id_str.zfill(6)
    filename = f"{name}_{padded_id}.mp4"
    filepath = os.path.join(folder_path, filename)
    
    if not os.path.exists(filepath):
        return ('missing', filename)
    
    # 生成新文件名
    id_int = int(id_str)
    start_time = id_int * 1000
    end_time = (id_int + 10) * 1000
    new_filename = f"{name}_{start_time}_{end_time}.mp4"
    new_filepath = os.path.join(output_folder, new_filename)
    
    # 复制文件
    try:
        shutil.copy2(filepath, new_filepath)
        return ('copied', filename, new_filename)
    except Exception as e:
        return ('error', filename, str(e))


def main():
    parser = argparse.ArgumentParser(description='检查CSV中指定的视频文件是否存在，并复制到新文件夹')
    parser.add_argument('csv_file', help='输入的CSV文件路径')
    parser.add_argument('folder_path', help='要搜索的文件夹路径')
    parser.add_argument('output_folder', help='输出文件夹路径')
    parser.add_argument('--workers', type=int, default=None, help='进程数，默认为CPU核心数')
    parser.add_argument('--num-slices', type=int, default=1, help='切片总数，将任务均分成多少份')
    parser.add_argument('--slice-id', type=int, default=0, help='当前处理的切片ID（从0开始）')
    args = parser.parse_args()
    
    csv_file = args.csv_file
    folder_path = args.folder_path
    output_folder = args.output_folder
    num_workers = args.workers or cpu_count()
    num_slices = args.num_slices
    slice_id = args.slice_id
    
    # 验证切片参数
    if num_slices < 1:
        print("错误: --num-slices 必须大于等于1")
        return
    if slice_id < 0 or slice_id >= num_slices:
        print(f"错误: --slice-id 必须在 0 到 {num_slices - 1} 之间")
        return
    
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)
    
    # 读取CSV文件
    all_tasks = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                name = row[0]
                id_str = row[1]
                all_tasks.append((name, id_str, folder_path, output_folder))
    
    total_records = len(all_tasks)
    
    # 计算当前切片的范围
    slice_size = total_records // num_slices
    remainder = total_records % num_slices
    
    # 分配余数：前 remainder 个切片各多分一个任务
    if slice_id < remainder:
        start_idx = slice_id * (slice_size + 1)
        end_idx = start_idx + slice_size + 1
    else:
        start_idx = remainder * (slice_size + 1) + (slice_id - remainder) * slice_size
        end_idx = start_idx + slice_size
    
    # 获取当前切片的任务
    tasks = all_tasks[start_idx:end_idx]
    
    print(f"共读取 {total_records} 条记录")
    print(f"切片设置: 共 {num_slices} 份，当前处理第 {slice_id} 份")
    print(f"当前切片范围: [{start_idx}, {end_idx})，共 {len(tasks)} 条记录")
    print(f"使用 {num_workers} 个进程进行处理")
    print(f"输出目录: {output_folder}")
    
    if len(tasks) == 0:
        print("当前切片没有任务需要处理")
        return
    
    # 多进程处理文件
    with Pool(num_workers) as pool:
        results = list(tqdm(
            pool.imap(process_file, tasks),
            total=len(tasks),
            desc=f"处理文件 (切片 {slice_id}/{num_slices})"
        ))
    
    # 统计结果
    missing_files = []
    copied_files = []
    error_files = []
    
    for result in results:
        if result[0] == 'missing':
            missing_files.append(result[1])
        elif result[0] == 'copied':
            copied_files.append((result[1], result[2]))
        elif result[0] == 'error':
            error_files.append((result[1], result[2]))
    
    # 打印不存在的文件
    if missing_files:
        print("\n不存在的文件:")
        for filename in missing_files:
            print(f"  {filename}")
    
    # 打印复制失败的文件
    if error_files:
        print("\n复制失败的文件:")
        for filename, error in error_files:
            print(f"  {filename}: {error}")
    
    # 统计
    print(f"\n当前切片统计 (切片 {slice_id}):")
    print(f"  处理总数: {len(tasks)} 个文件")
    print(f"  成功复制: {len(copied_files)} 个文件")
    print(f"  不存在: {len(missing_files)} 个文件")
    print(f"  复制失败: {len(error_files)} 个文件")


if __name__ == '__main__':
    main()