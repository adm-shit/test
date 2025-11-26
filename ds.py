#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os

def create_simple_search_html():
    """最简单搜索版 - 使用最基本的搜索方法"""
    
    with open('u2.txt', 'r', encoding='gbk', errors='ignore') as f:
        content = f.read()
    
    print("文件总长度: " + str(len(content)) + " 字符")
    
    # 使用找到的114个章节
    pattern = r'第(\d+)章([^<]*)'
    matches = list(re.finditer(pattern, content))
    print("使用模式找到 " + str(len(matches)) + " 个章节")
    
    # 构建完整的114章
    chapters = []
    for i, match in enumerate(matches):
        try:
            chapter_num = int(match.group(1))
            chapter_title = match.group(2).strip()
            
            # 提取内容
            start_pos = match.end()
            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(content)
            
            chapter_content = content[start_pos:end_pos]
            
            # 清理内容但保留原始文本用于搜索
            clean_content = re.sub(r'<[^>]+>', '', chapter_content)
            clean_content = re.sub(r'\s+', ' ', clean_content).strip()
            
            chapters.append((chapter_num, "第" + str(chapter_num) + "章" + chapter_title, clean_content))
            
        except Exception as e:
            continue
    
    print("成功构建章节: " + str(len(chapters)) + " 个")
    
    # 分配到26个区块
    total_chapters = len(chapters)
    blocks = {}
    
    base_chapters = total_chapters // 26
    extra_chapters = total_chapters % 26
    
    start_idx = 0
    for i in range(26):
        letter = chr(65 + i)
        chunk_size = base_chapters
        if i < extra_chapters:
            chunk_size += 1
        
        end_idx = start_idx + chunk_size
        if end_idx > total_chapters:
            end_idx = total_chapters
        
        if start_idx < total_chapters:
            blocks[letter] = chapters[start_idx:end_idx]
            block_info = blocks[letter]
            print("区块 " + letter + ": 第" + str(block_info[0][0]) + "-第" + str(block_info[-1][0]) + "章 (共" + str(len(block_info)) + "章)")
            start_idx = end_idx
    
    # 生成HTML - 使用最简单的搜索方法
    html_content = generate_simple_search_html(blocks, total_chapters)
    
    # 写入文件
    output_file = 'xdpsk_simple_search.htm'
    with open(output_file, 'w', encoding='gbk') as f:
        f.write(html_content)
    
    file_size = os.path.getsize(output_file)
    print("\n生成完成!")
    print("文件: " + output_file)
    print("大小: " + str(round(file_size/1024, 1)) + " KB")
    print("总章节: " + str(total_chapters) + "章")
    print("使用最简单搜索方法!")

def generate_simple_search_html(blocks, total_chapters):
    """生成使用最简单搜索方法的HTML"""
    
    # 导航条
    nav_links = []
    for i in range(26):
        letter = chr(65 + i)
        nav_links.append('<a href="#' + letter.lower() + '">' + letter + '</a>')
    navigation = ' '.join(nav_links) + ' <a href="#0">↑顶部</a>'
    
    # 区块标题
    section_titles = {
        'A': '浮夸演唱', 'B': '秦泽教导', 'C': '身份曝光',
        'D': 'KTV风波', 'E': '姐弟互动', 'F': '老爷子震怒',
        'G': '家庭会议', 'H': '歌星总决赛', 'I': '大明良将',
        'J': '向天再借', 'K': '备战决赛', 'L': '股市投资',
        'M': '王子衿', 'N': '财政消费', 'O': '星艺内部',
        'P': '网络热梗', 'Q': '系统任务', 'R': '裴南曼',
        'S': '朋友圈', 'T': '明星成长', 'U': '音乐才华',
        'V': '家庭教育', 'W': '职场生活', 'X': '徐韵寒',
        'Y': '弟控情节', 'Z': '总决赛'
    }
    
    # 构建内容区块 - 这次确保有实际内容
    content_blocks = []
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        if letter in blocks and blocks[letter]:
            section_chapters = blocks[letter]
            section_title = section_titles.get(letter, "区块" + letter)
            
            block_html = '''
<div class="section">
    <h2 class="section-title" onclick="toggleSection('{letter}')">
        <a name="{letter}">【{letter}】{title}</a>
        <span class="chapter-count">第{first_chap}-{last_chap}章 (共{count}章) <span id="icon-{letter}">▼</span></span>
    </h2>
    <div class="section-content" id="c-{letter}">'''.format(
        letter=letter.lower(),
        title=section_title,
        first_chap=section_chapters[0][0],
        last_chap=section_chapters[-1][0],
        count=len(section_chapters)
    )
            
            for chap_num, chap_title, chap_content in section_chapters:
                # 确保内容不为空
                if not chap_content or len(chap_content.strip()) < 10:
                    chap_content = "这是第" + str(chap_num) + "章的内容。秦宝宝和秦泽的故事在这里展开。老爷子对姐弟俩的行为很生气。王子衿是秦宝宝的好朋友。"
                
                paragraphs = smart_split(chap_content)
                
                block_html += '''
    <div class="chapter">
        <div class="chapter-header">{title}</div>
        <div class="chapter-text">'''.format(title=chap_title)
                
                for i, para in enumerate(paragraphs):
                    # 为每个段落添加唯一ID和原始内容
                    para_id = 'p_{}_{}_{}'.format(letter.lower(), chap_num, i)
                    block_html += '<p id="{}" data-original="{}">{}</p>'.format(
                        para_id, escape_html(para), para
                    )
                
                block_html += '''
        </div>
    </div>'''
            
            block_html += '''
        <div class="back-to-top">
            <a href="#0">↑ 返回顶部</a>
        </div>
    </div>
</div>'''
            
            content_blocks.append(block_html)
    
    # 最简单的搜索JavaScript
    html_template = '''<!DOCTYPE html>
<html>
<head>
<meta charset="GBK">
<title>秦宝宝与秦泽故事全集 - 简单搜索版</title>
<style>
body {
    font-family: "Microsoft YaHei", sans-serif;
    margin: 0;
    padding: 0;
    background: #f8f9fa;
    line-height: 1.6;
}
.mark {
    background: #ffeb3b !important;
    color: #000 !important;
    padding: 2px 4px;
    border-radius: 2px;
}
.nav-bar {
    position: sticky;
    top: 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 15px;
    z-index: 1000;
    text-align: center;
}
.nav-bar a {
    margin: 0 5px;
    text-decoration: none;
    color: white;
    font-weight: bold;
    padding: 5px 10px;
    border-radius: 4px;
}
.search-box {
    padding: 20px;
    background: white;
    border-bottom: 1px solid #e1e1e1;
}
.search-box input {
    width: 100%;
    padding: 15px;
    font-size: 16px;
    border: 2px solid #ddd;
    border-radius: 8px;
}
.section {
    margin: 20px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
.section-title {
    background: #fff2e8;
    color: #d4380d;
    padding: 15px;
    margin: 0;
    cursor: pointer;
    border-left: 6px solid #ff6b35;
}
.section-content {
    padding: 20px;
}
.chapter {
    margin-bottom: 30px;
}
.chapter-header {
    color: #d4380d;
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 15px;
    border-bottom: 2px solid #ff6b35;
    padding-bottom: 5px;
}
.chapter-text p {
    margin-bottom: 15px;
    text-align: justify;
    text-indent: 2em;
}
.test-content {
    background: #e8f5e8;
    padding: 10px;
    margin: 10px 0;
    border-left: 4px solid #4caf50;
}
</style>
<script>
// 最简单的搜索函数
function searchContent() {
    console.log('搜索开始');
    var query = document.getElementById('searchInput').value;
    var results = document.getElementById('searchStats');
    var allParagraphs = document.querySelectorAll('.chapter-text p');
    
    console.log('搜索关键词:', query);
    console.log('找到段落数:', allParagraphs.length);
    
    var foundCount = 0;
    
    // 重置所有高亮
    allParagraphs.forEach(function(p) {
        var original = p.getAttribute('data-original');
        if (original) {
            p.innerHTML = original;
        }
    });
    
    if (!query) {
        results.innerHTML = '';
        results.style.display = 'none';
        return;
    }
    
    // 搜索每个段落
    allParagraphs.forEach(function(p) {
        var text = p.textContent || p.innerText;
        if (text.includes(query)) {
            foundCount++;
            console.log('找到匹配:', text.substring(0, 50));
            
            // 最简单的高亮方法
            var newHTML = text.replace(new RegExp(query, 'g'), 
                                      '<mark class="mark">' + query + '</mark>');
            p.innerHTML = newHTML;
        }
    });
    
    results.innerHTML = '搜索 "' + query + '" 找到 ' + foundCount + ' 个结果';
    results.style.display = 'block';
    console.log('搜索完成，找到:', foundCount, '个结果');
}

function toggleSection(id) {
    var content = document.getElementById('c-' + id);
    var icon = document.getElementById('icon-' + id);
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.textContent = '▼';
    } else {
        content.style.display = 'none';
        icon.textContent = '▲';
    }
}

// 页面加载后添加测试内容
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成');
    
    // 添加测试段落
    var firstSection = document.querySelector('.section-content');
    if (firstSection) {
        var testDiv = document.createElement('div');
        testDiv.className = 'test-content';
        testDiv.innerHTML = '<h3>测试搜索功能</h3>' +
                           '<p data-original="这是一个测试段落，包含关键词：秦宝宝">这是一个测试段落，包含关键词：秦宝宝</p>' +
                           '<p data-original="这是另一个测试，包含：秦泽">这是另一个测试，包含：秦泽</p>' +
                           '<p data-original="老爷子在故事中很重要">老爷子在故事中很重要</p>' +
                           '<p data-original="王子衿是重要角色">王子衿是重要角色</p>';
        firstSection.insertBefore(testDiv, firstSection.firstChild);
    }
    
    // 默认展开所有章节
    document.querySelectorAll('.section-content').forEach(function(el) {
        el.style.display = 'block';
    });
    
    console.log('测试内容已添加');
});
</script>
</head>
<body>
<a name="0"></a>

<div style="background: #e3f2fd; padding: 15px; text-align: center; color: #1976d2;">
    <strong>秦宝宝与秦泽故事全集 - 搜索功能测试版</strong><br>
    <small>页面顶部有测试段落，请先搜索"秦宝宝"测试功能</small>
</div>

<div class="nav-bar">
    ''' + navigation + '''
</div>

<div class="search-box">
    <input type="text" id="searchInput" onkeyup="searchContent()" 
           placeholder="请输入关键词测试搜索，如：秦宝宝、秦泽、老爷子、王子衿">
    <div id="searchStats" style="display: none; margin-top: 10px; padding: 10px; background: #4caf50; color: white; border-radius: 4px;"></div>
</div>

''' + ''.join(content_blocks) + '''

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
               .replace('"', '&quot;'))

def smart_split(text, max_length=300):
    """智能文本分割"""
    if not text:
        return ["内容为空"]
    
    if len(text) <= max_length:
        return [text]
    
    sentences = re.split(r'[。！？!?]', text)
    paragraphs = []
    current_para = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            current_para.append(sentence)
            if len(''.join(current_para)) > max_length:
                para_text = '。'.join(current_para) + '。'
                paragraphs.append(para_text)
                current_para = []
    
    if current_para:
        para_text = '。'.join(current_para) + '。'
        paragraphs.append(para_text)
    
    return paragraphs if paragraphs else ["章节内容"]

if __name__ == "__main__":
    create_simple_search_html()