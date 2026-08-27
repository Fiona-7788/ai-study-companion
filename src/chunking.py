def chunk_text(text, max_length=200):
    # 先按段落分(空行或换行)
    paragraphs = text.split('\n')
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # 如果加上这段还在长度限制内,拼进当前chunk
        if len(current_chunk) + len(para) <= max_length:
            current_chunk += para + " "
        else:
            # 超了,先把当前chunk存起来,新开一个
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + " "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks