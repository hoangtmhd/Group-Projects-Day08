# Hướng dẫn Dữ liệu (Data Guide) - Nhóm RAG Chatbot

Tài liệu này cung cấp chi tiết về danh sách nguồn, quy tắc lọc dữ liệu và mẫu định dạng dữ liệu chuẩn hóa của phần việc Thu thập và chuẩn hóa dữ liệu do **Thái Minh** phụ trách, nhằm bàn giao cho nhóm để phục vụ các bước Indexing, Retrieval và Citation của Chatbot.

---

## 1. Danh sách Nguồn Dữ liệu (Data Sources)

Dữ liệu thô được lưu trữ tại thư mục [data/landing/](file:///media/minhnht31/data/vinuni/Group-Projects-Day08/data/landing/) bao gồm 2 nhóm chính:

### A. Văn bản Pháp luật (Legal Documents)
Được tải trực tiếp dưới định dạng PDF từ các cổng thông tin pháp luật chính thống tại Việt Nam:
1. **Bộ luật Hình sự 2015 (sửa đổi 2017) - Chương XX (Các tội phạm về ma tuý)**
   - *Tên file:* `bo-luat-hinh-su-2015-chuong-xx.pdf`
   - *Nguồn tham khảo:* [Thư viện Pháp luật](https://thuvienphapluat.vn)
2. **Luật Phòng, chống ma tuý 2021 (73/2021/QH15)**
   - *Tên file:* `luat-phong-chong-ma-tuy-2021.pdf`
   - *Nguồn tham khảo:* [Cổng thông tin điện tử Chính phủ](https://vanban.chinhphu.vn)
3. **Nghị định 105/2021/NĐ-CP (Hướng dẫn thi hành một số điều của Luật Phòng, chống ma túy)**
   - *Tên file:* `nghi-dinh-105-2021.pdf`
   - *Nguồn tham khảo:* [Cổng thông tin điện tử Bộ Tư pháp](https://moj.gov.vn)
4. **Nghị định 57/2022/NĐ-CP (Danh mục các chất ma túy và tiền chất)**
   - *Tên file:* `nghi-dinh-57-2022.pdf`
   - *Nguồn tham khảo:* [Cổng thông tin điện tử Chính phủ](https://vanban.chinhphu.vn)

### B. Tin tức báo chí (News Articles)
Crawl trực tiếp dưới dạng JSON (chứa thông tin metadata và văn bản markdown thô) từ các trang báo lớn:
1. **Diễn viên Hữu Tín bị bắt vì sử dụng ma túy** (VnExpress)
   - *Tên file:* `article_01.json`
   - *URL:* `https://vnexpress.net/dien-vien-huu-tin-bi-bat-vi-su-dung-ma-tuy-4478143.html`
2. **Ca sĩ Chí Dân bị tạm giữ liên quan ma túy** (VnExpress)
   - *Tên file:* `article_02.json`
   - *URL:* `https://vnexpress.net/ca-si-chi-dan-bi-tam-giu-4589258.html`
3. **Nghệ sĩ bị xử lý vì liên quan đến ma túy** (VnExpress)
   - *Tên file:* `article_03.json`
   - *URL:* `https://vnexpress.net/nghe-si-bi-xu-ly-vi-lien-quan-ma-tuy-4600000.html`
4. **Thu giữ ma túy tại nhà riêng của ca sĩ Chí Dân** (Tuổi Trẻ)
   - *Tên file:* `article_04.json`
   - *URL:* `https://tuoitre.vn/thu-giu-ma-tuy-tai-nha-rieng-cua-ca-si-chi-dan-2023040409413693.htm`
5. **Diễn viên Hữu Tín lãnh án tù vì tổ chức sử dụng trái phép chất ma túy** (Thanh Niên)
   - *Tên file:* `article_05.json`
   - *URL:* `https://thanhnien.vn/dien-vien-huu-tin-lanh-an-tu-vi-to-chuc-su-dung-trai-phep-chat-ma-tuy-185230420165507971.htm`
6. **Bí mật cuộc sống nghệ sĩ Việt sau scandal ma túy** (VnExpress)
   - *Tên file:* `article_06.json`
   - *URL:* `https://vnexpress.net/bi-mat-cuoc-song-nghe-si-viet-sau-scandal-ma-tuy-4710000.html`
7. **Tổng hợp nghệ sĩ Việt liên quan đến ma túy qua các năm** (VTC News)
   - *Tên file:* `article_07.json`
   - *URL:* `https://vtc.vn/nghe-si-viet-lien-quan-ma-tuy-ar800000.html`

---

## 2. Quy tắc lọc Dữ liệu (Data Filtering Rules)

Để đảm bảo dữ liệu chất lượng cao, hạn chế nhiễu trước khi đưa vào mô hình ngôn ngữ (LLM), chúng tôi áp dụng các quy tắc sau:

### Quy tắc lọc Văn bản Pháp luật:
- **Tính cập nhật:** Chỉ chọn các văn bản pháp luật hiện hành hoặc mới nhất (ví dụ: Luật Phòng, chống ma túy 2021 thay thế cho luật cũ).
- **Tính khu biệt:** Lọc đúng phần chương, điều quy định về hành vi ma túy và mức hình phạt (như Chương XX Bộ luật hình sự).
- **Loại bỏ nhiễu:** Khi chuyển sang markdown, lọc bỏ các dòng tiêu đề trang (header), số trang (footer) và các ký tự scan bị lỗi để tránh làm hỏng cấu trúc phân đoạn (chunking).

### Quy tắc lọc Tin tức:
- **Độ dài nội dung:** Văn bản thuần của tin tức sau khi làm sạch phải đạt **tối thiểu 500 ký tự**. Nếu lỗi crawl hoặc quá ngắn, hệ thống sẽ sử dụng nội dung tóm tắt chuẩn bị sẵn (fallback template).
- **Làm sạch HTML/CSS:** Loại bỏ tất cả các tag `<script>`, `<style>`, ảnh quảng cáo, các đề xuất bài viết liên quan (Recommended articles) và phần bình luận của độc giả.
- **Chuẩn hóa Metadata:** Mỗi file JSON thô trong thư mục landing bắt buộc phải lưu 4 thông tin: `url`, `title`, `date_crawled`, `content_markdown`.

---

## 3. Mẫu dữ liệu đã được chuẩn hóa (Standardized Output Sample)

Toàn bộ dữ liệu sau khi chạy qua module xử lý được lưu tại thư mục [data/standardized/](file:///media/minhnht31/data/vinuni/Group-Projects-Day08/data/standardized/).

### A. Mẫu dữ liệu chuẩn hóa của Tin tức (News Markdown)
Các file `.md` trong thư mục `news` bắt buộc chứa metadata header ở đầu file để LLM trích xuất nguồn trích dẫn:

```markdown
# Ca sĩ Chí Dân bị tạm giữ liên quan ma tuý

**Source:** https://vnexpress.net/ca-si-chi-dan-bi-tam-giu-4589258.html
**Crawled:** 2026-06-08T17:34:15.123456

---

Công an TP HCM đang tạm giữ ca sĩ Chí Dân cùng một số người khác để điều tra về hành vi liên quan đến việc sử dụng trái phép chất ma túy. 

Theo nguồn tin từ cơ quan chức năng, vụ việc được phát hiện khi lực lượng tuần tra kiểm tra hành chính một địa điểm trên địa bàn quận 3 và phát hiện nhóm người có dấu hiệu sử dụng chất cấm...
```

### B. Mẫu dữ liệu chuẩn hóa của Pháp luật (Legal Markdown)
Các file `.md` trong thư mục `legal` giữ nguyên cấu trúc văn bản hành chính để giúp Reranker dễ so khớp các Điều luật:

```markdown
# LUẬT PHÒNG, CHỐNG MA TÚY 2021

## CHƯƠNG I: QUY ĐỊNH CHUNG

### Điều 1. Phạm vi điều chỉnh
Luật này quy định về phòng, chống ma túy; quản lý người sử dụng trái phép chất ma túy; cai nghiện ma túy; trách nhiệm của cá nhân, gia đình, cơ quan, tổ chức trong phòng, chống ma túy; quản lý nhà nước và hợp tác quốc tế về phòng, chống ma túy.

### Điều 2. Giải thích từ ngữ
Trong Luật này, các từ ngữ dưới đây được hiểu như sau:
1. Chất ma túy là chất gây nghiện, chất hướng thần được quy định trong danh mục chất ma túy do Chính phủ ban hành...
```
