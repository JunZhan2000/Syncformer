import csv
import os
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import argparse


def check_file_exists(args):
    """检查单个文件是否存在"""
    name, id_str, folder_path = args
    # 将id填充到6位
    padded_id = id_str.zfill(6)
    filename = f"{name}_{padded_id}.mp4"
    filepath = os.path.join(folder_path, filename)
    
    if not os.path.exists(filepath):
        return (name, id_str)
    return None


def generate_txt_line(name, id_str):
    """根据name和id生成txt文件中的行格式"""
    id_int = int(id_str)
    return f"{name}_{id_int * 1000}_{(id_int + 10) * 1000}"


def main():
    parser = argparse.ArgumentParser(description='检查CSV中指定的视频文件是否存在并清理相关数据')
    parser.add_argument('csv_file', help='输入的CSV文件路径')
    parser.add_argument('folder_path', help='要搜索的文件夹路径')
    parser.add_argument('--workers', type=int, default=None, help='进程数，默认为CPU核心数')
    parser.add_argument('--output-dir', '-o', default='./cleaned_data', help='输出文件夹路径，默认为./cleaned_data')
    args = parser.parse_args()
    
    csv_file = args.csv_file
    folder_path = args.folder_path
    num_workers = args.workers or cpu_count()
    output_dir = args.output_dir
    
    # 创建输出文件夹
    os.makedirs(output_dir, exist_ok=True)
    
    # 读取CSV文件
    tasks = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                name = row[0]
                id_str = row[1]
                tasks.append((name, id_str, folder_path))
    
    print(f"共读取 {len(tasks)} 条记录")
    print(f"使用 {num_workers} 个进程进行检查")
    
    # 多进程检查文件
    with Pool(num_workers) as pool:
        results = list(tqdm(
            pool.imap(check_file_exists, tasks),
            total=len(tasks),
            desc="检查文件"
        ))
    
    # 收集不存在的文件信息
    missing_files = [item for item in results if item is not None]
    
    # 创建用于快速查找的集合
    # CSV格式: (name, id_str)
    missing_csv_set = set(missing_files)
    # TXT格式: 生成的行字符串
    missing_txt_set = set(generate_txt_line(name, id_str) for name, id_str in missing_files)
    
    print(f"\n缺失文件数量: {len(missing_files)}")
    
    # 需要处理的文件列表
    data_dir = "./data"
    txt_files = [
        os.path.join(data_dir, "vggsound_test.txt"),
        os.path.join(data_dir, "vggsound_train.txt"),
        os.path.join(data_dir, "vggsound_valid.txt"),
    ]
    csv_file_to_clean = os.path.join(data_dir, "vggsound.csv")
    
    # 处理TXT文件
    for txt_file in txt_files:
        if not os.path.exists(txt_file):
            print(f"文件不存在，跳过: {txt_file}")
            continue
        
        filename = os.path.basename(txt_file)
        output_path = os.path.join(output_dir, filename)
        
        original_count = 0
        kept_count = 0
        
        with open(txt_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        original_count = len(lines)
        
        # 过滤掉缺失的行
        kept_lines = []
        for line in lines:
            line_stripped = line.strip()
            if line_stripped not in missing_txt_set:
                kept_lines.append(line)
        
        kept_count = len(kept_lines)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(kept_lines)
        
        print(f"处理 {filename}: {original_count} -> {kept_count} (删除 {original_count - kept_count} 行)")
    
    # 处理CSV文件
    if os.path.exists(csv_file_to_clean):
        filename = os.path.basename(csv_file_to_clean)
        output_path = os.path.join(output_dir, filename)
        
        original_count = 0
        kept_count = 0
        
        kept_rows = []
        with open(csv_file_to_clean, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                original_count += 1
                if len(row) >= 2:
                    name = row[0]
                    id_str = row[1]
                    if (name, id_str) not in missing_csv_set:
                        kept_rows.append(row)
                else:
                    # 保留格式不正确的行
                    kept_rows.append(row)
        
        kept_count = len(kept_rows)
        
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(kept_rows)
        
        print(f"处理 {filename}: {original_count} -> {kept_count} (删除 {original_count - kept_count} 行)")
    else:
        print(f"文件不存在，跳过: {csv_file_to_clean}")
    
    # 保存缺失文件列表
    missing_list_path = os.path.join(output_dir, "missing_files.txt")
    with open(missing_list_path, 'w', encoding='utf-8') as f:
        for name, id_str in missing_files:
            f.write(f"{name},{id_str}\n")
    
    # 打印统计信息
    print(f"\n总计: {len(tasks)} 个文件")
    print(f"存在: {len(tasks) - len(missing_files)} 个文件")
    print(f"不存在: {len(missing_files)} 个文件")
    print(f"\n所有清理后的文件已保存到: {output_dir}")
    print(f"缺失文件列表已保存到: {missing_list_path}")


if __name__ == '__main__':
    main()