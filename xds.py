#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import sys
import time
from pathlib import Path

def process_large_html_file(input_file, output_file=None):
    """处理大型HTML文件 - 适用于411MB+的文件"""
    
    if not os.path.exists(input_file):
        print(f"错误: 输入文件 '{input_file}' 不存在")
        return
    
    # 自动生成输出文件名
    if output_file is None:
        input_path = Path(input_file)
        output_file = input_path.stem + "_search.html"
    
    print(f"开始处理文件: {input_file}")
    file_size = os.path.getsize(input_file)
    print(f"文件大小: {file_size / (1024*1024):.2f} MB")
    
    start_time = time.time()
    
    # 使用智能编码检测读取文件
    content = read_file_smart_encoding(input_file)
    if content is None:
        print("错误: 无法读取文件，请检查文件编码")
        return
    
    print(f"文件读取完成，总长度: {len(content)} 字符")
    
    # 提取章节 - 使用更通用的模式
    chapters = extract_chapters(content)
    print(f"成功提取章节: {len(chapters)} 个")
    
    if len(chapters) == 0:
        print("警告: 未找到章节，将创建单章节文件")
        chapters = [(1, "全文内容", content[:500000])]  # 限制内容长度
    
    # 分配到区块
    blocks = distribute_to_blocks(chapters)
    
    # 生成HTML
    html_content = generate_search_html(blocks, len(chapters), input_file)
    
    # 写入文件 - 使用UTF-8编码避免编码问题
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        output_size = os.path.getsize(output_file)
        processing_time = time.time() - start_time
        
        print("\n处理完成!")
        print(f"输出文件: {output_file}")
        print(f"输出大小: {output_size / 1024:.1f} KB")
        print(f"总章节: {len(chapters)} 章")
        print(f"处理时间: {processing_time:.1f} 秒")
        print("功能: 支持全文搜索 + 导航链接 + 章节锚点 + 字体调整 + 折叠功能 + 彩色文本 + 加粗文本")
        
    except Exception as e:
        print(f"写入文件时出错: {e}")

def read_file_smart_encoding(file_path):
    """智能检测文件编码并读取 - 不使用外部库"""
    try:
        # 读取二进制数据
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        
        # 常见编码列表（按优先级排序）
        encodings_to_try = [
            'utf-8', 
            'gbk', 
            'gb2312', 
            'gb18030',
            'big5',
            'latin1',
            'cp1252'
        ]
        
        best_content = None
        best_encoding = None
        best_score = 0
        
        for encoding in encodings_to_try:
            try:
                content = raw_data.decode(encoding, errors='replace')
                score = evaluate_encoding_quality(content)
                
                print(f"编码 {encoding}: 质量得分 {score:.2f}")
                
                if score > best_score:
                    best_score = score
                    best_content = content
                    best_encoding = encoding
                    
                # 如果质量很好，直接使用
                if score > 0.9:
                    break
                    
            except (UnicodeDecodeError, LookupError) as e:
                print(f"编码 {encoding} 失败: {e}")
                continue
        
        if best_content is not None:
            print(f"选择最佳编码: {best_encoding} (质量得分: {best_score:.2f})")
            return best_content
        else:
            # 如果所有编码都失败，使用替代模式
            print("所有编码尝试失败，使用替代模式...")
            return raw_data.decode('utf-8', errors='replace')
        
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return None

def evaluate_encoding_quality(text):
    """评估编码质量"""
    if not text or len(text) < 100:
        return 0
    
    score = 0.0
    
    # 1. 检查常见中文字符
    common_chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    chinese_ratio = common_chinese_chars / len(text)
    score += min(chinese_ratio * 10, 0.4)  # 最多0.4分
    
    # 2. 检查常见中文标点和词语
    common_chinese_patterns = [
        r'的', r'了', r'是', r'在', r'和', r'有', r'不', r'我', r'你', r'他',
        r'，', r'。', r'！', r'？', r'；', r'：', r'「', r'」', r'《', r'》'
    ]
    
    pattern_count = 0
    for pattern in common_chinese_patterns:
        pattern_count += len(re.findall(pattern, text))
    
    if len(text) > 0:
        pattern_ratio = pattern_count / len(text)
        score += min(pattern_ratio * 20, 0.3)  # 最多0.3分
    
    # 3. 检查乱码字符（扣分）
    garbled_chars = len(re.findall(r'�|[-¿]|[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', text))
    garbled_ratio = garbled_chars / len(text) if len(text) > 0 else 0
    score -= min(garbled_ratio * 10, 0.3)  # 最多扣0.3分
    
    # 4. 检查常见的HTML结构和章节模式（加分）
    html_patterns = [
        r'<div', r'<p>', r'<br', r'<h[1-6]', r'第[零一二三四五六七八九十百千\d]+章',
        r'<title>', r'<body>', r'<html>'
    ]
    
    html_count = 0
    for pattern in html_patterns:
        html_count += len(re.findall(pattern, text, re.IGNORECASE))
    
    html_ratio = html_count / (len(text) / 1000)  # 每1000字符的密度
    score += min(html_ratio * 0.1, 0.2)  # 最多0.2分
    
    # 确保分数在0-1之间
    return max(0.0, min(1.0, score))

def extract_chapters(content):
    """提取章节 - 使用更强大的模式"""
    chapters = []
    
    # 清理内容，移除明显的乱码
    content = clean_garbled_text(content)
    
    # 多种章节模式 - 更全面的匹配
    patterns = [
        # 中文章节格式
        r'第[零一二三四五六七八九十百千\d]+章[^\n<]*',
        r'第[零一二三四五六七八九十百千\d]+回[^\n<]*',
        r'第[零一二三四五六七八九十百千\d]+节[^\n<]*',
        
        # 数字章节格式
        r'第\d+章[^\n<]*',
        r'第\d+回[^\n<]*', 
        r'第\d+节[^\n<]*',
        
        # HTML标题格式
        r'<h[12][^>]*>第[零一二三四五六七八九十百千\d]+[章节回][^<]*</h[12]>',
        r'<h[12][^>]*>第\d+[章节回][^<]*</h[12]>',
        
        # 英文章节格式
        r'Chapter\s+\d+[^\n<]*',
        r'Section\s+\d+[^\n<]*',
    ]
    
    all_matches = []
    for pattern in patterns:
        try:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            all_matches.extend(matches)
            if matches:
                print(f"模式 '{pattern[:20]}...' 找到 {len(matches)} 个匹配")
        except Exception as e:
            continue
    
    if not all_matches:
        print("未找到标准章节格式，尝试查找所有标题...")
        # 查找所有可能的标题行
        title_patterns = [
            r'<h[123][^>]*>.*?</h[123]>',
            r'<div[^>]*class=[\'"][^\'"]*title[^\'"]*[\'"][^>]*>.*?</div>',
            r'<p[^>]*class=[\'"][^\'"]*title[^\'"]*[\'"][^>]*>.*?</p>',
        ]
        
        for pattern in title_patterns:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            all_matches.extend(matches)
            if matches:
                print(f"标题模式找到 {len(matches)} 个匹配")
    
    if not all_matches:
        print("使用段落分割创建章节")
        return split_by_paragraphs(content)
    
    # 去重并排序
    unique_matches = []
    seen_positions = set()
    
    for match in sorted(all_matches, key=lambda x: x.start()):
        if match.start() not in seen_positions:
            unique_matches.append(match)
            seen_positions.add(match.start())
    
    print(f"去重后找到 {len(unique_matches)} 个唯一章节")
    
    # 处理找到的章节
    for i, match in enumerate(unique_matches):
        try:
            chapter_num = i + 1
            full_text = match.group(0)
            
            # 提取标题文本
            title_text = extract_title_text(full_text)
            
            # 提取内容
            start_pos = match.end()
            if i < len(unique_matches) - 1:
                end_pos = unique_matches[i + 1].start()
            else:
                end_pos = len(content)
            
            chapter_content = content[start_pos:end_pos]
            
            # 清理内容
            clean_content = clean_html_content(chapter_content)
            
            # 如果标题为空，使用默认标题
            if not title_text.strip():
                title_text = f"第{chapter_num}章"
            else:
                title_text = f"第{chapter_num}章 {title_text}"
            
            chapters.append((chapter_num, title_text, clean_content))
            
        except Exception as e:
            print(f"处理章节 {i+1} 时出错: {e}")
            continue
    
    return chapters

def clean_garbled_text(text):
    """清理乱码文本"""
    if not text:
        return ""
    
    # 移除常见的乱码字符序列
    garbled_patterns = [
        r'[�]',  # 替换字符
        r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]',  # 控制字符
    ]
    
    for pattern in garbled_patterns:
        text = re.sub(pattern, '', text)
    
    return text

def extract_title_text(html_text):
    """从HTML标签中提取纯文本标题"""
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', html_text)
    # 清理空白字符和乱码
    text = re.sub(r'\s+', ' ', text).strip()
    text = clean_garbled_text(text)
    return text

def split_by_paragraphs(content, max_chapters=200):
    """如果没有章节，按段落分割"""
    print("使用段落分割创建伪章节")
    
    # 清理内容
    content = clean_garbled_text(content)
    
    # 多种段落分割方式
    paragraphs = []
    
    # 尝试按HTML段落分割
    p_matches = list(re.finditer(r'<p[^>]*>(.*?)</p>', content, re.DOTALL))
    if len(p_matches) > 10:
        for match in p_matches:
            text = clean_html_content(match.group(1))
            if len(text.strip()) > 20:
                paragraphs.append(text)
    else:
        # 按换行符分割
        paragraphs = re.split(r'\n\s*\n', content)
    
    chapters = []
    for i in range(min(len(paragraphs), max_chapters)):
        clean_content = clean_html_content(paragraphs[i])
        clean_content = clean_garbled_text(clean_content)
        if len(clean_content.strip()) > 10:
            chapters.append((i+1, f"第{i+1}段", clean_content))
    
    return chapters

def clean_html_content(content):
    """清理HTML内容"""
    if not content:
        return "内容为空"
    
    # 移除HTML标签但保留文本
    clean_content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
    clean_content = re.sub(r'<style[^>]*>.*?</style>', '', clean_content, flags=re.DOTALL)
    clean_content = re.sub(r'<[^>]+>', ' ', clean_content)
    
    # 合并空白字符
    clean_content = re.sub(r'\s+', ' ', clean_content)
    clean_content = clean_content.strip()
    
    if not clean_content:
        clean_content = "本章节内容"
    
    return clean_content

def distribute_to_blocks(chapters, num_blocks=26):
    """将章节分配到区块"""
    total_chapters = len(chapters)
    blocks = {}
    
    if total_chapters == 0:
        return blocks
    
    # 如果章节数少于区块数，每个区块放1章
    if total_chapters <= num_blocks:
        for i, chapter in enumerate(chapters):
            letter = chr(65 + i)  # A, B, C...
            blocks[letter] = [chapter]
            print(f"区块 {letter}: 第{chapter[0]}章 (共1章)")
        return blocks
    
    base_chapters = total_chapters // num_blocks
    extra_chapters = total_chapters % num_blocks
    
    start_idx = 0
    for i in range(num_blocks):
        letter = chr(65 + i)  # A-Z
        chunk_size = base_chapters
        if i < extra_chapters:
            chunk_size += 1
        
        end_idx = start_idx + chunk_size
        if end_idx > total_chapters:
            end_idx = total_chapters
        
        if start_idx < total_chapters:
            blocks[letter] = chapters[start_idx:end_idx]
            block_info = blocks[letter]
            print(f"区块 {letter}: 第{block_info[0][0]}-第{block_info[-1][0]}章 (共{len(block_info)}章)")
            start_idx = end_idx
    
    return blocks

def generate_search_html(blocks, total_chapters, original_filename):
    """生成搜索HTML - 包含导航链接和锚点"""
    
    # 生成导航链接 - A-Z 区块导航
    nav_links = []
    for i in range(26):
        letter = chr(65 + i)
        if letter in blocks and blocks[letter]:
            first_chap = blocks[letter][0][0]
            last_chap = blocks[letter][-1][0]
            nav_links.append(f'<a href="#block-{letter}" title="第{first_chap}-{last_chap}章">{letter}</a>')
    
    # 添加顶部链接 | ->.
    nav_links.append('<a href="#top">顶部</a>')
    navigation = '.'.join(nav_links) 
    
    # 内容区块
    content_blocks = []
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        if letter in blocks and blocks[letter]:
            section_chapters = blocks[letter]
            
            block_html = f'''
<div class="block" id="block-{letter}">
    <h2 class="block-title" onclick="toggleBlock('{letter}')">
        <span class="block-letter rainbow-text">{letter}</span>
        <span class="block-range gradient-text">第{section_chapters[0][0]}-第{section_chapters[-1][0]}章</span>
        <span class="block-count color-text-3">(共{len(section_chapters)}章)</span>
        <span class="block-controls">
            <span class="fold-icon color-text-4" id="icon-{letter}">▼</span>
            <a href="#top" class="top-link color-text-5">↑顶部</a>
        </span>
    </h2>
    <div class="block-content" id="content-{letter}">'''
            
            for chap_num, chap_title, chap_content in section_chapters:
                # 为每个章节创建锚点
                chapter_anchor = f"chap-{chap_num}"
                paragraphs = smart_split(chap_content)
                
                block_html += f'''
    <div class="chapter" id="{chapter_anchor}">
        <h6 class="chapter-header" onclick="toggleChapter('{letter}-{chap_num}')">
            <span class="chapter-title color-text-1">{escape_html(chap_title)}</span>
            <span class="chapter-links">
                <span class="fold-icon color-text-4" id="chapter-icon-{letter}-{chap_num}">▼</span>
                <a href="#{chapter_anchor}" class="anchor-link color-text-2" title="章节链接">#</a>
                <a href="#top" class="top-link color-text-5">↑</a>
            </span>
        </h6>
        <div class="chapter-text" id="chapter-content-{letter}-{chap_num}">'''
                
                for i, para in enumerate(paragraphs):
                    para_id = f'p_{letter}_{chap_num}_{i}'
                    escaped_para = escape_html(para)
                    # 为段落添加随机颜色类
                    color_class = f'color-text-{(i % 6) + 1}'
                    block_html += f'<p id="{para_id}" class="{color_class}" data-original="{escaped_para}">{para}</p>'
                
                block_html += '''
        </div>
    </div>'''
            
            block_html += '''
    </div>
</div>'''
            
            content_blocks.append(block_html)
    
    # 将所有内容区块连接成一个字符串
    content_html = ''.join(content_blocks)
    
    # 如果没有内容区块，创建默认内容
    if not content_html:
        content_html = '''
<div class="block" id="block-default">
    <h2 class="block-title" onclick="toggleBlock('default')">
        <span class="block-letter rainbow-text">全</span>
        <span class="block-range gradient-text">全文内容</span>
        <span class="block-controls">
            <span class="fold-icon color-text-4" id="icon-default">▼</span>
            <a href="#top" class="top-link color-text-5">↑顶部</a>
        </span>
    </h2>
    <div class="block-content" id="content-default">
        <div class="chapter" id="chap-1">
            <h6 class="chapter-header" onclick="toggleChapter('default-1')">
                <span class="chapter-title color-text-1">全文内容</span>
                <span class="chapter-links">
                    <span class="fold-icon color-text-4" id="chapter-icon-default-1">▼</span>
                    <a href="#chap-1" class="anchor-link color-text-2" title="章节链接">#</a>
                    <a href="#top" class="top-link color-text-5">↑</a>
                </span>
            </h6>
            <div class="chapter-text" id="chapter-content-default-1">
                <p class="color-text-3">文件内容加载成功，请使用搜索功能查找特定内容。</p>
            </div>
        </div>
    </div>
</div>'''
    
    # HTML模板
    html_template = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>全文搜索版 - {escape_html(original_filename)}</title>
<style>
/* 重置样式 */
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: "Microsoft YaHei", "SimHei", sans-serif;
    line-height: 1.6;
    color: #333;
    background: #f8f9fa;
    font-size: 29px; /* 26默认字体大小 */
    transition: font-size 0.3s ease;
}}

/* 字体大小类 */
.font-small {{
    font-size: 20px !important;
}}

.font-normal {{
    font-size: 28px !important;
}}

.font-large {{
    font-size: 34px !important;
}}

.font-xlarge {{
    font-size: 38px !important;
}}

/* 加粗文本类 */
.text-bold {{
    font-weight: bold !important;
}}

.text-normal {{
    font-weight: normal !important;
}}

/* 彩色文本系统 */
.rainbow-text {{
    background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4, #FFEAA7, #DDA0DD);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: bold;
}}

.gradient-text {{
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: bold;
}}

.color-text-1 {{ color: #E74C3C !important; }} /* 红色 */
.color-text-2 {{ color: #2980B9 !important; }} /* 蓝色 */
.color-text-3 {{ color: #27AE60 !important; }} /* 绿色 */
.color-text-4 {{ color: #8E44AD !important; }} /* 紫色 */
.color-text-5 {{ color: #E67E22 !important; }} /* 橙色 */
.color-text-6 {{ color: #16A085 !important; }} /* 青色 */

/* 高亮样式 */
.mark {{
    background: grey !important;
    color: #000 !important;
    padding: 2px 4px;
    border-radius: 3px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.2);
}}

/* 顶部导航 - 单行紧凑设计#ffeb3b */
.header {{
    background: linear-gradient(135deg, grey 0%, grey 100%);
    color: white;
    padding: 2px 11px; /* 6 15进一步减少内边距#667eea  #764ba2*/
    position: sticky;
    top: 0;
    z-index: 1000;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    min-height: 16px; /* 40进一步缩小高度 */
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
}}

.header-title {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: bold;
}}

.header-icon {{
    font-size: 12px;  /* 18缩小字体 */
}}

.header-text {{
    font-size: 12px; /* 16缩小字体 */
    white-space: nowrap;
}}

.header-subtitle {{
    font-size: 12px; /* 缩小字体 */
    opacity: 0.9;
    white-space: nowrap;
}}

/* 控制栏 - 进一步缩小 */
.control-bar {{
    background: white;
    padding: 5px 15px; /* 进一步减少内边距 */
    border-bottom: 1px solid #e1e1e1;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px; /* 减少间距 */
    min-height: 15px; /* 35进一步缩小高度 */
}}

.control-group {{
    display: flex;
    align-items: center;
    gap: 6px; /* 减少间距 */
}}

.control-label {{
    font-weight: bold;
    color: #666;
    font-size: 12px; /* 缩小字体 */
}}

.control-btn {{
    background: #667eea;
    color: white;
    border: none;
    padding: 4px 8px; /* 进一步减少内边距 */
    border-radius: 3px;
    cursor: pointer;
    font-size: 11px; /* 缩小字体 #5a6fd8*/
    transition: all 0.3s;
}}

.control-btn:hover {{
    background: grey;
    transform: translateY(-1px);
}}

.control-btn.active {{
    background: #ff6b35;
}}

.font-controls {{
    display: flex;
    gap: 2px; /* 减少间距 */
}}

.font-btn {{
    background: #f0f0f0;
    border: 1px solid #ddd;
    padding: 3px 6px; /* 进一步减少内边距 */
    border-radius: 2px;
    cursor: pointer;
    font-size: 10px; /* 缩小字体 */
    transition: all 0.3s;
}}

.font-btn:hover {{
    background: #e0e0e0;
}}

.font-btn.active {{
    background: #667eea;
    color: white;
    border-color: #667eea;
}}

.bold-controls {{
    display: flex;
    gap: 2px;
}}

.bold-btn {{
    background: #f0f0f0;
    border: 1px solid #ddd;
    padding: 3px 8px;
    border-radius: 2px;
    cursor: pointer;
    font-size: 10px;
    transition: all 0.3s;
}}

.bold-btn:hover {{
    background: #e0e0e0;
}}

.bold-btn.active {{
    background: #667eea;
    color: white;
    border-color: #667eea;
}}

/* 主导航 - 进一步缩小 */
.main-nav {{
    background: rgba(255,255,255,0.1);
    padding: 2px 4px; /* 4 10进一步减少内边距 */
    margin: 4px -11px -6px -11px; /* 15调整外边距 */
    backdrop-filter: blur(10px);
    text-align: center;
    min-height: 11px; /* 25进一步缩小高度 */
}}

.main-nav a {{
    color: white;
    text-decoration: none;
    margin: 0 3px; /* 减少间距 */
    padding: 2px 3px; /* 2 6进一步减少内边距 */
    border-radius: 2px;
    transition: background 0.3s;
    display: inline-block;
    font-size: 11px; /* 缩小字体 */
}}

.main-nav a:hover {{
    background: rgba(255,255,255,0.2);
    transform: translateY(-1px);
}}

/* 搜索框 - 进一步缩小 */
.search-box {{
    background: white;
    padding: 6px 14px; /* 10 20进一步减少内边距 */
    border-bottom: 1px solid #e1e1e1;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    min-height: 35px; /* 55进一步缩小高度 */
}}

.search-container {{
    max-width: 800px;
    margin: 0 auto;
}}

.search-box input {{
    width: 100%;
    padding: 8px 15px; /* 进一步减少内边距 */
    font-size: 14px; /* 缩小字体 */
    border: 2px solid #e1e1e1;
    border-radius: 18px; /* 减小圆角 */
    outline: none;
    transition: all 0.3s;
}}

.search-box input:focus {{
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}}

.search-stats {{
    margin-top: 8px; /* 减少上边距 */
    padding: 6px 12px; /* 减少内边距 */
    background: #4caf50;
    color: white;
    border-radius: 4px; /* 减小圆角 */
    display: none;
    text-align: center;
    font-size: 12px; /* 缩小字体 */
}}

.search-stats.error {{
    background: #f44336;
}}

/* 区块样式 - 进一步缩小 */
.block {{
    margin: 10px; /* 减少外边距 */
    background: white;
    border-radius: 6px; /* 减小圆角 */
    box-shadow: 0 1px 5px rgba(0,0,0,0.1); /* 减小阴影 */
    overflow: hidden;
    transition: transform 0.2s;
}}

.block:hover {{
    transform: translateY(-1px);
}}

.block-title {{
    background: linear-gradient(135deg, #f8edeb, #f7931e);
    color: white;
    padding: 4px 8px; /*#ff6b35/f8!! 8 12进一步减少内边距 */
    margin: 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 6px; /* 减少间距 */
    cursor: pointer;
    transition: background 0.3s;
    min-height: 26px; /* 40进一步缩小高度 */
}}

.block-title:hover {{
    background: linear-gradient(135deg, #e55a2b, #e0841a);
}}

.block-letter {{
    font-size: 14px; /* 18缩小字体 */
    font-weight: bold;
    background: rgba(255,255,255,0.2);
    padding: 4px 8px; /* 减少内边距 */
    border-radius: 4px; /* 减小圆角 */
    min-width: 22px; /* 30减小最小宽度 */
    text-align: center;
}}

.block-range {{
    font-size: 14px; /* 缩小字体 */
    font-weight: bold;
    flex-grow: 1;
}}

.block-count {{
    opacity: 0.9;
    font-size: 12px; /* 缩小字体 */
}}

.block-controls {{
    display: flex;
    align-items: center;
    gap: 6px; /* 减少间距 */
}}

.fold-icon {{
    font-size: 10px; /* 缩小字体 */
    transition: transform 0.3s;
    cursor: pointer;
    user-select: none;
}}

.fold-icon.collapsed {{
    transform: rotate(-90deg);
}}

.top-link {{
    color: white;
    text-decoration: none;
    padding: 3px 6px; /* 减少内边距 */
    background: rgba(255,255,255,0.2);
    border-radius: 3px; /* 减小圆角 */
    font-size: 10px; /* 缩小字体 */
    transition: background 0.3s;
}}

.top-link:hover {{
    background: rgba(255,255,255,0.3);
}}

.block-content {{
    padding: 0;
    transition: max-height 0.3s ease;
}}

.block-content.collapsed {{
    max-height: 0;
    overflow: hidden;
}}

/* 章节样式 - 进一步缩小 */
.chapter {{
    border-bottom: 1px solid #f0f0f0;
    transition: background-color 0.3s;
}}

.chapter:last-child {{
    border-bottom: none;
}}

.chapter-header {{
    color: grey;
    font-size: 16px; /* #d4380d缩小字体 */
    font-weight: bold;
    margin: 0;
    padding: 10px 15px; /* 进一步减少内边距 */
    border-bottom: 1px solid grey; /* #ff6b35减小边框 */
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 6px; /* 减少间距 */
    cursor: pointer;
    transition: background 0.3s;
    min-height: 26px; /* 40进一步缩小高度 */
}}

.chapter-header:hover {{
    background: grey; /* #fff8f0;* /
}}

.chapter-title {{
    flex-grow: 1;
}}

.chapter-links {{
    display: flex;
    align-items: center;
    gap: 6px; /* 减少间距 */
}}

.chapter-text {{
    padding: 0 15px; /* 减少内边距 */
    transition: max-height 0.3s ease;
    overflow: hidden;
}}

.chapter-text.collapsed {{
    max-height: 0;
    padding: 0 15px;
}}

.chapter-text p {{
    margin-bottom: 8px; /* 减少下边距 */
    text-align: justify;
    text-indent: 2em;
    line-height: 1.5; /* 减小行高 */
    font-size: inherit;
    padding: 1px 0; /* 添加小内边距 */
}}

/* 响应式设计 */
@media (max-width: 768px) {{
    .block {{
        margin: 5px;
    }}
    
    .chapter-header {{
        font-size: 14px;
        flex-direction: column;
        align-items: flex-start;
        padding: 8px 12px;
        min-height: 25px;
    }}
    
    .chapter-links {{
        align-self: flex-end;
    }}
    
    .main-nav {{
        padding: 3px 8px;
        min-height: 16px; /*30?*/
    }}
    
    .main-nav a {{
        margin: 1px;
        padding: 1px 4px;
        font-size: 6px; /*9*/
    }}
    
    .block-title {{
        flex-direction: column;
        gap: 4px;
        text-align: center;
        padding: 6px 10px;
        min-height: 25px;
    }}
    
    .control-bar {{
        flex-direction: column;
        align-items: stretch;
        gap: 4px;
        padding: 4px 12px;
        min-height: 14px; /*30*/
    }}
    
    .control-group {{
        justify-content: center;
    }}
    
    .header {{
        padding: 4px 12px;
        min-height: 25px;
        flex-direction: column;
        gap: 2px;
    }}
    
    .header-title {{
        flex-direction: column;
        gap: 2px;
        text-align: center;
    }}
    
    .header-text {{
        font-size: 10px; /*14*/
    }}
    
    .search-box {{
        padding: 8px 15px;
        min-height: 25px;
    }}
}}
</style>
</head>
<body>
<div class="header" id="top">
    <!div class="header-title">
        <!span class="header-icon" /span>
        <!span class="header-text"Rt【全文搜索版】 {escape_html(original_filename)} | 总章节: {total_chapters} 章 /span>
    <!/div>
    <div class="main-nav">
        {navigation}
    </div>
</div>

<div class="control-bar">
    <div class="control-group">
        <span class="control-label">字体:</span>
        <div class="font-controls">
            <button class="font-btn" onclick="setFontSize('small')">小</button>
            <button class="font-btn active" onclick="setFontSize('normal')">中</button>
            <button class="font-btn" onclick="setFontSize('large')">大</button>
            <button class="font-btn" onclick="setFontSize('xlarge')">特大</button>
        </div>
    </div>
    <div class="control-group">
        <span class="control-label">加粗:</span>
        <div class="bold-controls">
            <button class="bold-btn active" onclick="setBoldText('normal')">正常</button>
            <button class="bold-btn" onclick="setBoldText('bold')">加粗</button>
        </div>
    </div>
    <div class="control-group">
        <span class="control-label">折叠:</span>
        <button class="control-btn" onclick="expandAll()">展开所有</button>
        <button class="control-btn" onclick="collapseAll()">折叠所有</button>
        <button class="control-btn" onclick="toggleAllBlocks()">切换区块</button>
        <button class="control-btn" onclick="toggleAllChapters()">切换章节</button>
    </div>
</div>

<div class="search-box">
    <div class="search-container">
        <input type="text" id="searchInput" onkeyup="performSearchWithDebounce()" 
               placeholder="请输入关键词搜索... (如：章、第、人物名等)">
        <div id="searchStats" class="search-stats"></div>
    </div>
</div>

{content_html}

<script>
// 字体大小控制
let currentFontSize = 'normal';
let currentBoldText = 'normal';

function setFontSize(size) {{
    // 移除所有字体类
    document.body.classList.remove('font-small', 'font-normal', 'font-large', 'font-xlarge');
    // 添加新字体类
    document.body.classList.add(`font-${{size}}`);
    currentFontSize = size;
    
    // 更新按钮状态
    document.querySelectorAll('.font-btn').forEach(btn => {{
        btn.classList.remove('active');
    }});
    event.target.classList.add('active');
}}

// 加粗文本控制
function setBoldText(style) {{
    // 移除所有加粗类
    document.body.classList.remove('text-bold', 'text-normal');
    // 添加新加粗类
    document.body.classList.add(`text-${{style}}`);
    currentBoldText = style;
    
    // 更新按钮状态
    document.querySelectorAll('.bold-btn').forEach(btn => {{
        btn.classList.remove('active');
    }});
    event.target.classList.add('active');
}}

// 折叠展开功能
function toggleBlock(blockId) {{
    const content = document.getElementById(`content-${{blockId}}`);
    const icon = document.getElementById(`icon-${{blockId}}`);
    
    if (content.classList.contains('collapsed')) {{
        content.classList.remove('collapsed');
        icon.classList.remove('collapsed');
        icon.textContent = '▼';
    }} else {{
        content.classList.add('collapsed');
        icon.classList.add('collapsed');
        icon.textContent = '▶';
    }}
}}

function toggleChapter(chapterId) {{
    const content = document.getElementById(`chapter-content-${{chapterId}}`);
    const icon = document.getElementById(`chapter-icon-${{chapterId}}`);
    
    if (content.classList.contains('collapsed')) {{
        content.classList.remove('collapsed');
        icon.classList.remove('collapsed');
        icon.textContent = '▼';
    }} else {{
        content.classList.add('collapsed');
        icon.classList.add('collapsed');
        icon.textContent = '▶';
    }}
}}

// 批量控制函数
function expandAll() {{
    document.querySelectorAll('.block-content').forEach(el => {{
        el.classList.remove('collapsed');
    }});
    document.querySelectorAll('.chapter-text').forEach(el => {{
        el.classList.remove('collapsed');
    }});
    document.querySelectorAll('.fold-icon').forEach(el => {{
        el.classList.remove('collapsed');
        el.textContent = '▼';
    }});
}}

function collapseAll() {{
    document.querySelectorAll('.block-content').forEach(el => {{
        el.classList.add('collapsed');
    }});
    document.querySelectorAll('.chapter-text').forEach(el => {{
        el.classList.add('collapsed');
    }});
    document.querySelectorAll('.fold-icon').forEach(el => {{
        el.classList.add('collapsed');
        el.textContent = '▶';
    }});
}}

function toggleAllBlocks() {{
    const allCollapsed = Array.from(document.querySelectorAll('.block-content'))
        .every(el => el.classList.contains('collapsed'));
    
    document.querySelectorAll('.block-content').forEach(el => {{
        if (allCollapsed) {{
            el.classList.remove('collapsed');
        }} else {{
            el.classList.add('collapsed');
        }}
    }});
    
    document.querySelectorAll('.block-title .fold-icon').forEach(el => {{
        if (allCollapsed) {{
            el.classList.remove('collapsed');
            el.textContent = '▼';
        }} else {{
            el.classList.add('collapsed');
            el.textContent = '▶';
        }}
    }});
}}

function toggleAllChapters() {{
    const allCollapsed = Array.from(document.querySelectorAll('.chapter-text'))
        .every(el => el.classList.contains('collapsed'));
    
    document.querySelectorAll('.chapter-text').forEach(el => {{
        if (allCollapsed) {{
            el.classList.remove('collapsed');
        }} else {{
            el.classList.add('collapsed');
        }}
    }});
    
    document.querySelectorAll('.chapter-header .fold-icon').forEach(el => {{
        if (allCollapsed) {{
            el.classList.remove('collapsed');
            el.textContent = '▼';
        }} else {{
            el.classList.add('collapsed');
            el.textContent = '▶';
        }}
    }});
}}

// 增强搜索功能
function performSearch() {{
    const query = document.getElementById('searchInput').value.trim();
    const results = document.getElementById('searchStats');
    const allParagraphs = document.querySelectorAll('.chapter-text p');
    
    let foundCount = 0;
    let foundChapters = new Set();
    
    // 重置所有高亮
    allParagraphs.forEach(p => {{
        const original = p.getAttribute('data-original');
        if (original) {{
            p.innerHTML = original;
        }}
        p.closest('.chapter').style.backgroundColor = '';
    }});
    
    if (!query) {{
        results.innerHTML = '';
        results.style.display = 'none';
        return;
    }}
    
    // 搜索每个段落
    allParagraphs.forEach(p => {{
        const text = p.textContent || p.innerText;
        if (text.includes(query)) {{
            foundCount++;
            const chapter = p.closest('.chapter');
            if (chapter) {{
                foundChapters.add(chapter.id);
                // 自动展开包含搜索结果的章节
                const chapterContent = chapter.querySelector('.chapter-text');
                const chapterIcon = chapter.querySelector('.chapter-header .fold-icon');
                if (chapterContent && chapterContent.classList.contains('collapsed')) {{
                    chapterContent.classList.remove('collapsed');
                    if (chapterIcon) {{
                        chapterIcon.classList.remove('collapsed');
                        chapterIcon.textContent = '▼';
                    }}
                }}
            }}
            
            // 高亮匹配文本
            const newHTML = text.replace(new RegExp(escapeRegExp(query), 'g'), 
                '<mark class="mark">' + query + '</mark>');
            p.innerHTML = newHTML;
            
            // 高亮包含匹配的章节
            if (chapter) {{
                chapter.style.backgroundColor = '#f8ffd6';
            }}
        }}
    }});
    
    if (foundCount > 0) {{
        results.innerHTML = '✅ 搜索 "<b>' + query + '</b>" 找到 <b>' + foundCount + '</b> 个匹配，分布在 <b>' + foundChapters.size + '</b> 个章节中';
        results.style.display = 'block';
        results.className = 'search-stats';
    }} else {{
        results.innerHTML = '❌ 未找到包含 "<b>' + query + '</b>" 的内容';
        results.style.display = 'block';
        results.className = 'search-stats error';
    }}
}}

function escapeRegExp(string) {{
    return string.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&');
}}

// 平滑滚动到锚点
document.addEventListener('DOMContentLoaded', function() {{
    // 添加点击事件到锚点链接
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
        anchor.addEventListener('click', function (e) {{
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {{
                target.scrollIntoView({{
                    behavior: 'smooth',
                    block: 'start'
                }});
            }}
        }});
    }});
    
    console.log('页面加载完成！搜索功能已就绪。');
    console.log('总章节数:', {total_chapters});
}});

// 实时搜索防抖
let searchTimer;
function performSearchWithDebounce() {{
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {{
        performSearch();
    }}, 300);
}}
</script>
</body>
</html>'''
    
    return html_template

def escape_html(text):
    """转义HTML特殊字符"""
    if not text:
        return ""
    return (text.replace('&', '&amp;')
               .replace('<', '&lt;')
               .replace('>', '&gt;')
               .replace('"', '&quot;')
               .replace("'", '&#39;'))

def smart_split(text, max_length=500):
    """智能文本分割"""
    if not text or len(text.strip()) == 0:
        return ["内容为空"]
    
    text = text.strip()
    if len(text) <= max_length:
        return [text]
    
    # 按句子分割
    sentences = re.split(r'[。！？!?]', text)
    paragraphs = []
    current_para = []
    current_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            sentence_length = len(sentence)
            if current_length + sentence_length > max_length and current_para:
                para_text = '。'.join(current_para) + '。'
                paragraphs.append(para_text)
                current_para = [sentence]
                current_length = sentence_length
            else:
                current_para.append(sentence)
                current_length += sentence_length
    
    if current_para:
        para_text = '。'.join(current_para) + '。'
        paragraphs.append(para_text)
    
    return paragraphs if paragraphs else [text[:max_length] + "..."]

def main():
    """主函数"""
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        # 如果没有参数，使用当前目录下的第一个htm/html文件
        html_files = list(Path('.').glob('*.htm')) + list(Path('.').glob('*.html'))
        if html_files:
            input_file = str(html_files[0])
            output_file = None
            print(f"自动选择文件: {input_file}")
        else:
            print("用法: python ds.py <输入文件> [输出文件]")
            print("或直接将文件拖放到此脚本上")
            input("按回车退出...")
            return
    
    process_large_html_file(input_file, output_file)

if __name__ == "__main__":
    main()

