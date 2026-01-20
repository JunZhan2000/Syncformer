import os
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import argparse


def delete_file(filepath):
    """删除单个文件"""
    filename = os.path.basename(filepath)
    
    # 计算下划线数量
    underscore_count = filename.count('_')
    
    if underscore_count < 5:
        try:
            os.remove(filepath)
            return (filename, underscore_count, True, None)
        except Exception as e:
            return (filename, underscore_count, False, str(e))
    
    return None


def main():
    parser = argparse.ArgumentParser(description='删除文件夹下名字下划线少于5个的文件')
    parser.add_argument('folder_path', help='文件夹路径')
    parser.add_argument('--workers', type=int, default=None, help='进程数，默认为CPU核心数')
    parser.add_argument('--dry-run', action='store_true', help='仅预览，不实际删除')
    parser.add_argument('--ext', type=str, default=None, help='只处理指定扩展名的文件，如 .mp4')
    args = parser.parse_args()
    
    folder_path = args.folder_path
    num_workers = args.workers or cpu_count()
    dry_run = args.dry_run
    ext_filter = args.ext.lower() if args.ext else None
    
    # 获取所有文件
    all_files = []
    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        if os.path.isfile(filepath):
            if ext_filter is None or filename.lower().endswith(ext_filter):
                all_files.append(filepath)
    
    print(f"共找到 {len(all_files)} 个文件")
    print(f"使用 {num_workers} 个进程")
    
    # 统计待删除文件
    to_delete = []
    for filepath in all_files:
        filename = os.path.basename(filepath)
        if filename.count('_') < 5:
            to_delete.append(filepath)
    
    print(f"下划线少于5个的文件: {len(to_delete)} 个")
    
    if dry_run:
        print("\n[预览模式] 将删除以下文件:")
        for filepath in to_delete:
            filename = os.path.basename(filepath)
            count = filename.count('_')
            print(f"  {filename} (下划线数: {count})")
        return
    
    if len(to_delete) == 0:
        print("没有需要删除的文件")
        return
    
    # 多进程删除
    with Pool(num_workers) as pool:
        results = list(tqdm(
            pool.imap(delete_file, to_delete),
            total=len(to_delete),
            desc="删除文件"
        ))
    
    # 统计结果
    success_count = 0
    fail_count = 0
    
    print("\n删除结果:")
    for result in results:
        if result is not None:
            filename, count, success, error = result
            if success:
                success_count += 1
            else:
                fail_count += 1
                print(f"  失败: {filename} - {error}")
    
    print(f"\n总计待删除: {len(to_delete)} 个文件")
    print(f"成功删除: {success_count} 个")
    print(f"删除失败: {fail_count} 个")


if __name__ == '__main__':
    main()