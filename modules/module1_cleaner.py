import re
from operator import attrgetter

def extract_entities(text):
    """
    [DAY 18 - REGEX NÂNG CAO] Tự động quét tiêu đề để nhận diện các "ông lớn" công nghệ.
    """
    tags = []
    if re.search(r'\b(openai|chatgpt|gpt[-]?4[o]?)\b', text, re.IGNORECASE):
        tags.append("#OpenAI")
    if re.search(r'\b(google|gemini|deepmind|alphabet)\b', text, re.IGNORECASE):
        tags.append("#Google")
    if re.search(r'\b(microsoft|copilot|azure)\b', text, re.IGNORECASE):
        tags.append("#Microsoft")
    if re.search(r'\b(meta|llama|zuckerberg)\b', text, re.IGNORECASE):
        tags.append("#Meta")
    if re.search(r'\b(anthropic|claude)\b', text, re.IGNORECASE):
        tags.append("#Anthropic")
    if re.search(r'\bapple\b', text, re.IGNORECASE):
        tags.append("#Apple")
    if re.search(r'\$[\d]+[MB]?', text, re.IGNORECASE):
        tags.append("#Funding_Money")
    return tags

def clean_titles(articles_list):
    """
    [DAY 15] ĐỘ PHỨC TẠP THUẬT TOÁN (BIG-O NOTATION)
    - Set lookup (seen): O(1) thời gian tìm kiếm.
    - Duyệt mảng: O(N) với N là số lượng bài báo.
    - Tổng độ phức tạp Time: O(N) -> Rất nhanh!
    """
    seen = set() 
    cleaned_articles = []
    
    for article in articles_list:
        # Sử dụng NamedTuple: Truy cập bằng thuộc tính (article.title) cực nhanh
        raw_title = article.title
        if not raw_title: 
            continue
        
        # [DAY 18] Trích xuất AI Tag
        extracted_tags = extract_entities(raw_title)
        
        temp_title = re.sub(r'[^\w\s+\-&#.]', '', raw_title).lower().strip()        
        
        if temp_title not in seen:
            # [DAY 14] NamedTuple là Bất biến (Immutable). 
            # Bắt buộc dùng _replace() để tạo ra object mới ghi đè giá trị.
            cleaned_article = article._replace(title=temp_title, tags=extracted_tags)
            cleaned_articles.append(cleaned_article)
            seen.add(temp_title)
            
    # [DAY 16] THUẬT TOÁN SẮP XẾP (SORTING)
    # Tối ưu hóa hiệu suất: Dùng operator.attrgetter sẽ chạy trực tiếp ở nhân C (nhanh hơn 20% so với dùng lambda function thông thường)
    # Độ phức tạp Time (Timsort): O(N log N)
    cleaned_articles.sort(key=attrgetter('date'), reverse=True)
    
    return cleaned_articles