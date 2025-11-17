#  Copyright © [2024] 程序那些事
#
#  All rights reserved. This software and associated documentation files (the "Software") are provided for personal and educational use only. Commercial use of the Software is strictly prohibited unless explicit permission is obtained from the author.
#
#  Permission is hereby granted to any person to use, copy, and modify the Software for non-commercial purposes, provided that the following conditions are met:
#
#  1. The original copyright notice and this permission notice must be included in all copies or substantial portions of the Software.
#  2. Modifications, if any, must retain the original copyright information and must not imply that the modified version is an official version of the Software.
#  3. Any distribution of the Software or its modifications must retain the original copyright notice and include this permission notice.
#
#  For commercial use, including but not limited to selling, distributing, or using the Software as part of any commercial product or service, you must obtain explicit authorization from the author.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHOR OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#  Author: 程序那些事
#  email: flydean@163.com
#  Website: [www.flydean.com](http://www.flydean.com)
#  GitHub: [https://github.com/ddean2009/MoneyPrinterPlus](https://github.com/ddean2009/MoneyPrinterPlus)
#
#  All rights reserved.
#
#

import os
import subprocess
import random
import tempfile

import streamlit as st
import requests

from tools.file_utils import random_line_from_text_file, download_file_from_url
from tools.utils import get_must_session_option, random_with_system_time, extent_audio, run_ffmpeg_command

# 获取当前脚本的绝对路径
script_path = os.path.abspath(__file__)

# print("当前脚本的绝对路径是:", script_path)

# 脚本所在的目录
script_dir = os.path.dirname(script_path)
# 音频输出目录
audio_output_dir = os.path.join(script_dir, "../../work")
audio_output_dir = os.path.abspath(audio_output_dir)


def get_session_video_scene_text():
    video_dir_list = []
    video_text_list = []
    if 'scene_number' not in st.session_state:
        st.session_state['scene_number'] = 0
    for i in range(int(st.session_state.get('scene_number'))+1):
        print("select video scene " + str(i + 1))
        if "video_scene_folder_" + str(i + 1) in st.session_state and st.session_state["video_scene_folder_" + str(i + 1)] is not None:
            video_dir_list.append(st.session_state["video_scene_folder_" + str(i + 1)])
            video_text_list.append(st.session_state["video_scene_text_" + str(i + 1)])
    return video_dir_list, video_text_list


def get_video_scene_text_list(video_text_list):
    video_scene_text_list = []
    for video_text in video_text_list:
        if video_text is not None and video_text != "":
            # 检查是否是URL
            is_url = video_text.startswith('http://') or video_text.startswith('https://')
            
            if is_url:
                # 如果是URL，先下载到临时文件
                try:
                    # 创建临时文件
                    temp_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False, encoding='utf-8')
                    temp_file_path = temp_file.name
                    temp_file.close()
                    
                    # 下载文件
                    response = requests.get(video_text, stream=True, timeout=30)
                    if response.status_code == 200:
                        # 保存到临时文件
                        with open(temp_file_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        # 从临时文件读取
                        video_line = random_line_from_text_file(temp_file_path)
                        video_scene_text_list.append(video_line)
                        
                        # 删除临时文件
                        try:
                            os.remove(temp_file_path)
                        except:
                            pass
                    else:
                        print(f"无法下载文案文件: {video_text}, 状态码: {response.status_code}")
                        st.toast(f"无法下载文案文件: {video_text}", icon="⚠️")
                        video_scene_text_list.append("")
                except Exception as e:
                    print(f"下载或读取文案文件时出错: {e}")
                    st.toast(f"处理文案文件时出错: {str(e)}", icon="⚠️")
                    video_scene_text_list.append("")
                    # 清理临时文件
                    try:
                        if 'temp_file_path' in locals():
                            os.remove(temp_file_path)
                    except:
                        pass
            else:
                # 本地文件，直接读取
                video_line = random_line_from_text_file(video_text)
                video_scene_text_list.append(video_line)
        else:
            video_scene_text_list.append("")
    return video_scene_text_list


def get_video_text_from_list(video_scene_text_list):
    return " ".join(video_scene_text_list)


def extract_audio_from_video(video_file, output_audio_file):
    """
    从视频文件中提取音频（支持本地文件和URL）
    :param video_file: 视频文件路径或URL
    :param output_audio_file: 输出音频文件路径
    :return: 是否成功
    """
    try:
        # 如果是URL，ffmpeg可以直接处理，不需要检查文件是否存在
        is_url = video_file.startswith('http://') or video_file.startswith('https://')
        
        if not is_url and not os.path.exists(video_file):
            print(f"视频文件不存在: {video_file}")
            return False
        
        command = [
            'ffmpeg',
            '-i', video_file,
            '-vn',  # 不包含视频流
            '-acodec', 'pcm_s16le',  # 使用PCM编码
            '-ar', '16000',  # 采样率改为16kHz（腾讯云推荐）
            '-ac', '1',  # 单声道（腾讯云推荐）
            '-f', 'wav',  # 指定输出格式为WAV
            '-y',  # 覆盖输出文件
            output_audio_file
        ]
        
        # 对于URL，可能需要更长的超时时间
        # 不使用 text=True，因为 ffmpeg 输出可能包含非 UTF-8 字符
        result = subprocess.run(command, capture_output=True, timeout=300 if is_url else 60)
        if result.returncode == 0 and os.path.exists(output_audio_file):
            print(f"成功从视频提取音频: {video_file} -> {output_audio_file}")
            return True
        else:
            # 尝试解码错误信息，如果失败则使用默认编码
            try:
                error_msg = result.stderr.decode('utf-8', errors='ignore') if result.stderr else ''
                if not error_msg and result.stdout:
                    error_msg = result.stdout.decode('utf-8', errors='ignore')
            except:
                error_msg = f"FFmpeg返回码: {result.returncode}"
            print(f"提取音频失败: {error_msg}")
            return False
    except subprocess.TimeoutExpired:
        print(f"提取音频超时: {video_file}")
        return False
    except Exception as e:
        print(f"从视频提取音频时出错: {e}")
        return False


def get_video_files_from_dir(video_dir):
    """
    从视频目录中获取所有视频文件
    :param video_dir: 视频目录路径
    :return: 视频文件列表
    """
    video_files = []
    if os.path.exists(video_dir) and os.path.isdir(video_dir):
        for f in os.listdir(video_dir):
            if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv')):
                video_files.append(os.path.join(video_dir, f))
    return video_files


def is_video_file(path):
    """
    判断路径是否是视频文件（包括URL）
    :param path: 路径或URL
    :return: 是否是视频文件
    """
    if not path:
        return False
    # 检查是否是URL
    if path.startswith('http://') or path.startswith('https://'):
        # URL中如果包含视频扩展名，认为是视频文件
        video_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.webm', '.m4v')
        return any(path.lower().endswith(ext) for ext in video_extensions)
    # 检查是否是本地文件
    if os.path.isfile(path):
        return path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.webm', '.m4v'))
    return False


def is_image_file(path):
    """
    判断路径是否是图片文件（包括URL）
    :param path: 路径或URL
    :return: 是否是图片文件
    """
    if not path:
        return False
    # 检查是否是URL
    if path.startswith('http://') or path.startswith('https://'):
        # URL中如果包含图片扩展名，认为是图片文件
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
        return any(path.lower().endswith(ext) for ext in image_extensions)
    # 检查是否是本地文件
    if os.path.isfile(path):
        return path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'))
    return False


def extract_audio_from_video_dir(video_path, output_audio_file):
    """
    从视频路径或目录中提取音频
    :param video_path: 视频文件路径/URL 或视频目录路径
    :param output_audio_file: 输出音频文件路径
    :return: 是否成功
    """
    # 首先检查是否是图片文件（图片无法提取音频）
    if is_image_file(video_path):
        print(f"检测到图片文件/URL，无法提取音频: {video_path}")
        return False
    
    # 检查是否是单个视频文件（包括URL）
    if is_video_file(video_path):
        print(f"检测到视频文件/URL，直接提取音频: {video_path}")
        return extract_audio_from_video(video_path, output_audio_file)
    
    # 如果不是文件，检查是否是目录
    if os.path.exists(video_path) and os.path.isdir(video_path):
        video_files = get_video_files_from_dir(video_path)
        if not video_files:
            print(f"视频目录中没有找到视频文件: {video_path}")
            return False
        
        # 随机选择一个视频文件
        selected_video = random.choice(video_files)
        print(f"从视频目录中选择视频文件: {selected_video}")
        return extract_audio_from_video(selected_video, output_audio_file)
    
    # 既不是文件也不是目录
    print(f"路径既不是视频文件也不是目录: {video_path}")
    return False


def get_audio_and_video_list(audio_service, audio_rate):
    audio_output_file_list = []
    video_dir_list, video_text_list = get_session_video_scene_text()
    video_scene_text_list = get_video_scene_text_list(video_text_list)
    audio_voice = get_must_session_option("audio_voice", "请先设置配音语音")
    i = 0
    for idx, (video_scene_text, video_dir) in enumerate(zip(video_scene_text_list, video_dir_list)):
        temp_file_name = str(random_with_system_time()) + str(i)
        i = i + 1
        audio_output_file = os.path.join(audio_output_dir, str(temp_file_name) + ".wav")
        
        if video_scene_text is not None and video_scene_text != "":
            # 如果提供了文案，尝试使用文案生成音频
            print(f"场景 {idx + 1}: 尝试使用文案生成音频")
            try:
                audio_service.save_with_ssml(video_scene_text,
                                             audio_output_file,
                                             audio_voice,
                                             audio_rate)
                if os.path.exists(audio_output_file) and os.path.getsize(audio_output_file) > 0:
                    extent_audio(audio_output_file, 1)
                    audio_output_file_list.append(audio_output_file)
                    print(f"场景 {idx + 1}: 文案生成音频成功")
                else:
                    raise Exception("生成的音频文件为空或不存在")
            except Exception as e:
                # TTS服务失败
                error_msg = str(e)
                print(f"场景 {idx + 1}: 文案生成音频失败: {error_msg}")
                
                # 检查视频目录是否是图片文件
                if is_image_file(video_dir):
                    # 如果提供了文案但视频目录是图片，TTS失败时无法回退
                    error_msg = f"场景 {idx + 1} TTS服务失败（{error_msg}），且视频目录是图片文件无法提取音频。\n请修复TTS服务配置（如开通腾讯云TTS服务或更换其他TTS服务），或提供视频文件/URL而不是图片文件"
                    st.error(error_msg)
                    st.stop()
                else:
                    # 如果视频目录不是图片，可以尝试从视频提取音频作为回退
                    print(f"场景 {idx + 1}: 回退到从视频提取音频")
                    st.warning(f"场景 {idx + 1} TTS服务失败（{error_msg}），已自动切换到从视频提取音频")
                    
                    if extract_audio_from_video_dir(video_dir, audio_output_file):
                        extent_audio(audio_output_file, 1)
                        audio_output_file_list.append(audio_output_file)
                    else:
                        error_msg = f"场景 {idx + 1} 无法提取音频，请确保视频目录中有视频文件或提供视频文件/URL"
                        st.error(error_msg)
                        st.stop()
        else:
            # 如果没有提供文案，从视频目录中提取音频
            print(f"场景 {idx + 1}: 从视频目录提取音频")
            
            # 先检查是否是图片文件，如果是图片且没有文案，无法提取音频
            if is_image_file(video_dir):
                error_msg = f"场景 {idx + 1} 的视频目录是图片文件，无法提取音频。\n请提供视频片段文案路径，系统将使用文案生成音频；或者提供视频文件/URL而不是图片文件"
                st.error(error_msg)
                st.stop()
            
            if extract_audio_from_video_dir(video_dir, audio_output_file):
                extent_audio(audio_output_file, 1)
                audio_output_file_list.append(audio_output_file)
            else:
                error_msg = f"场景 {idx + 1} 无法提取音频，请提供视频文案或确保视频目录中有视频文件或提供视频文件/URL"
                st.error(error_msg)
                st.stop()

    return audio_output_file_list, video_dir_list


def get_audio_and_video_list_local(audio_service):
    audio_output_file_list = []
    video_dir_list, video_text_list = get_session_video_scene_text()
    video_scene_text_list = get_video_scene_text_list(video_text_list)
    i = 0
    for idx, (video_scene_text, video_dir) in enumerate(zip(video_scene_text_list, video_dir_list)):
        temp_file_name = str(random_with_system_time()) + str(i)
        i = i + 1
        audio_output_file = os.path.join(audio_output_dir, str(temp_file_name) + ".wav")
        
        if video_scene_text is not None and video_scene_text != "":
            # 如果提供了文案，尝试使用文案生成音频
            print(f"场景 {idx + 1}: 尝试使用文案生成音频")
            try:
                audio_service.chat_with_content(video_scene_text, audio_output_file)
                if os.path.exists(audio_output_file) and os.path.getsize(audio_output_file) > 0:
                    extent_audio(audio_output_file, 1)
                    audio_output_file_list.append(audio_output_file)
                    print(f"场景 {idx + 1}: 文案生成音频成功")
                else:
                    raise Exception("生成的音频文件为空或不存在")
            except Exception as e:
                # TTS服务失败
                error_msg = str(e)
                print(f"场景 {idx + 1}: 文案生成音频失败: {error_msg}")
                
                # 检查视频目录是否是图片文件
                if is_image_file(video_dir):
                    # 如果提供了文案但视频目录是图片，TTS失败时无法回退
                    error_msg = f"场景 {idx + 1} TTS服务失败（{error_msg}），且视频目录是图片文件无法提取音频。\n请修复TTS服务配置（如开通腾讯云TTS服务或更换其他TTS服务），或提供视频文件/URL而不是图片文件"
                    st.error(error_msg)
                    st.stop()
                else:
                    # 如果视频目录不是图片，可以尝试从视频提取音频作为回退
                    print(f"场景 {idx + 1}: 回退到从视频提取音频")
                    st.warning(f"场景 {idx + 1} TTS服务失败（{error_msg}），已自动切换到从视频提取音频")
                    
                    if extract_audio_from_video_dir(video_dir, audio_output_file):
                        extent_audio(audio_output_file, 1)
                        audio_output_file_list.append(audio_output_file)
                    else:
                        error_msg = f"场景 {idx + 1} 无法提取音频，请确保视频目录中有视频文件或提供视频文件/URL"
                        st.error(error_msg)
                        st.stop()
        else:
            # 如果没有提供文案，从视频目录中提取音频
            print(f"场景 {idx + 1}: 从视频目录提取音频")
            
            # 先检查是否是图片文件，如果是图片且没有文案，无法提取音频
            if is_image_file(video_dir):
                error_msg = f"场景 {idx + 1} 的视频目录是图片文件，无法提取音频。\n请提供视频片段文案路径，系统将使用文案生成音频；或者提供视频文件/URL而不是图片文件"
                st.error(error_msg)
                st.stop()
            
            if extract_audio_from_video_dir(video_dir, audio_output_file):
                extent_audio(audio_output_file, 1)
                audio_output_file_list.append(audio_output_file)
            else:
                error_msg = f"场景 {idx + 1} 无法提取音频，请提供视频文案或确保视频目录中有视频文件或提供视频文件/URL"
                st.error(error_msg)
                st.stop()
    
    return audio_output_file_list, video_dir_list


def get_video_text():
    video_dir_list, video_text_list = get_session_video_scene_text()
    video_scene_text_list = get_video_scene_text_list(video_text_list)
    return get_video_text_from_list(video_scene_text_list)


def concat_audio_list(audio_output_file_list):
    temp_output_file_name = os.path.join(audio_output_dir, str(random_with_system_time()) + ".wav")
    concat_audio_file = os.path.join(audio_output_dir, "concat_audio_file.txt")
    with open(concat_audio_file, 'w', encoding='utf-8') as f:
        for audio_file in audio_output_file_list:
            f.write("file '{}'\n".format(os.path.abspath(audio_file)))
    # 调用ffmpeg来合并音频
    # 注意：这里假设ffmpeg在你的PATH中，否则你需要提供ffmpeg的完整路径
    command = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_audio_file,
        '-c', 'copy',  # 如果可能，直接复制流而不是重新编码
        temp_output_file_name
    ]
    run_ffmpeg_command(command)
    # 完成后，删除临时文件（如果你不再需要它）
    os.remove(concat_audio_file)
    print(f"Audio files have been merged into {temp_output_file_name}")
    return temp_output_file_name
