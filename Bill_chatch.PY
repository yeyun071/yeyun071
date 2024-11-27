import requests
import os
import subprocess
import json

def check_ffmpeg():
    """检查是否安装了FFmpeg"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True)
        return True
    except FileNotFoundError:
        print("错误：未安装FFmpeg！请先安装FFmpeg并确保它在系统PATH中。")
        print("Windows安装指南：")
        print("1. 下载FFmpeg: https://www.gyan.dev/ffmpeg/builds/")
        print("2. 解压并将bin目录添加到系统环境变量PATH中")
        print("3. 重启终端后重试")
        return False

def get_video_info(bv_id):
    """获取视频信息"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.bilibili.com'
    }
    
    url = f'https://api.bilibili.com/x/web-interface/view?bvid={bv_id}'
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if data['code'] == 0:
            video_data = data['data']
            info = {
                '标题': video_data['title'],
                '作者': video_data['owner']['name'],
                '播放量': video_data['stat']['view'],
                '点赞数': video_data['stat']['like'],
                '投币数': video_data['stat']['coin'],
                '收藏数': video_data['stat']['favorite'],
                '简介': video_data['desc']
            }
            return info
        else:
            print(f"获取视频信息失败：{data['message']}")
            return None
            
    except Exception as e:
        print(f"获取视频信息时发生错误：{str(e)}")
        return None

def get_video_url(bvid):
    """获取视频下载地址"""
    url = f'https://api.bilibili.com/x/player/pagelist?bvid={bvid}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.bilibili.com'
    }
    
    try:
        response = requests.get(url, headers=headers)
        cid = response.json()['data'][0]['cid']
        
        playurl_url = 'https://api.bilibili.com/x/player/playurl'
        params = {
            'bvid': bvid,
            'cid': cid,
            'qn': 80,  # 视频质量，80为1080p
            'fnval': 16  # 返回格式，16为dash格式
        }
        
        response = requests.get(playurl_url, headers=headers, params=params)
        video_data = response.json()
        
        if video_data['code'] == 0:
            video_url = video_data['data']['dash']['video'][0]['baseUrl']
            audio_url = video_data['data']['dash']['audio'][0]['baseUrl']
            return video_url, audio_url
        else:
            print(f"获取视频地址失败：{video_data['message']}")
            return None, None
            
    except Exception as e:
        print(f"获取视频地址时发生错误：{str(e)}")
        return None, None

def download_video(bvid, output_dir='downloads'):
    """下载并合并视频"""
    if not check_ffmpeg():
        return False

    # 获取视频信息
    video_info = get_video_info(bvid)
    if not video_info:
        return False
    
    # 创建下载目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    video_url, audio_url = get_video_url(bvid)
    if not video_url or not audio_url:
        return False
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.bilibili.com'
    }
    
    try:
        # 下载视频
        print("正在下载视频流...")
        video_content = requests.get(video_url, headers=headers).content
        video_path = os.path.join(output_dir, f'{bvid}_video.mp4')
        with open(video_path, 'wb') as f:
            f.write(video_content)
        
        # 下载音频
        print("正在下载音频流...")
        audio_content = requests.get(audio_url, headers=headers).content
        audio_path = os.path.join(output_dir, f'{bvid}_audio.mp3')
        with open(audio_path, 'wb') as f:
            f.write(audio_content)
        
        # 合并视频和音频
        print("正在合并音视频...")
        # 使用视频标题作为文件名（去除非法字符）
        safe_title = "".join([c for c in video_info['标题'] if c.isalnum() or c in (' ', '-', '_')]).rstrip()
        output_path = os.path.join(output_dir, f'{safe_title}.mp4')
        
        try:
            subprocess.run([
                'ffmpeg', '-i', video_path, 
                '-i', audio_path, 
                '-c:v', 'copy', 
                '-c:a', 'aac', 
                output_path
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg合并失败：{e.stderr.decode()}")
            return False
        
        # 删除临时文件
        if os.path.exists(output_path):
            os.remove(video_path)
            os.remove(audio_path)
            print(f"下载完成！文件保存在：{output_path}")
            
            # 保存视频信息
            info_path = os.path.join(output_dir, f'{safe_title}_info.json')
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(video_info, f, ensure_ascii=False, indent=2)
            print(f"视频信息已保存到：{info_path}")
            
            return True
        else:
            print("合并后的文件未找到！")
            return False
            
    except Exception as e:
        print(f"下载失败：{str(e)}")
        # 清理临时文件
        for file in [video_path, audio_path]:
            if os.path.exists(file):
                os.remove(file)
        return False

if __name__ == '__main__':
    bvid = input("请输入要下载的视频BV号：")  # 例如：BV12VS1YvEHw
    download_video(bvid)