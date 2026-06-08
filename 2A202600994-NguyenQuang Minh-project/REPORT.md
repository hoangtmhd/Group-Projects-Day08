# BÁO CÁO TỔNG HỢP TIẾN ĐỘ DỰ ÁN (TASK 4 - TASK 10)

Đây là báo cáo tổng hợp quá trình triển khai hệ thống RAG Pipeline Pháp luật & Báo chí.

---

# Hoàn thành Task 4: Chunking & Indexing

Đã hoàn thành xuất sắc việc phân mảnh dữ liệu (Chunking) và Vector hóa (Embedding) để lưu trữ vào Vector Store, làm tiền đề vững chắc cho hệ thống RAG Pipeline.

## Các thay đổi chính

- **Chuyển đổi sang OpenAI API**: Sau khi gặp giới hạn quá khắt khe của Gemini API (chỉ 100 requests/phút trên gói miễn phí), chúng ta đã chuyển sang sử dụng API của OpenAI (`text-embedding-3-small`). Điều này cho phép tạo embedding hàng loạt với tốc độ cực nhanh.
- **Nâng cấp Weaviate**: Gỡ bỏ phiên bản Docker Weaviate 1.24.4 cũ và thay bằng bản 1.27.0 để tương thích hoàn toàn với thư viện `weaviate-client` v4 mới nhất. Chạy thành công Weaviate trên cổng `8081`.
- **Hoàn thiện Code `task4_chunking_indexing.py`**:
  - Tự động đọc 10 file Markdown dữ liệu (báo chí và luật ma tuý).
  - Sử dụng Hybrid Chunking (Markdown Header + Kích thước 500 ký tự) tạo ra **1296 chunks**.
  - Gọi OpenAI API để nhúng 1296 chunks này vào không gian vector 1536 chiều.
  - Insert toàn bộ vào collection `DrugLawDocs` trong cơ sở dữ liệu Weaviate.

## Kết quả Verification

Tất cả 1296 mẩu văn bản dữ liệu đã nằm gọn gàng trong cơ sở dữ liệu Weaviate và đã sẵn sàng để truy vấn tìm kiếm (Search) trong các Task tiếp theo!

---

# Hoàn thành Task 5: Semantic Search (Tìm kiếm ngữ nghĩa)

Module tìm kiếm ngữ nghĩa đã được viết thành công và được cập nhật để đồng bộ với cấu hình ở Task 4.

## Các thay đổi chính

- **Cập nhật model OpenAI**: Đồng bộ thư viện `openai` và model `text-embedding-3-small` để đảm bảo hệ thống nhúng truy vấn (query) bằng đúng mô hình đã nhúng dữ liệu gốc.
- **Kết nối Weaviate**: Đã định tuyến kết nối tìm kiếm tới cổng `8081` (grpc: `50052`) mà Docker Weaviate đang chạy.
- **Lấy kết quả theo Cosine Similarity**: Trích xuất chính xác các tham số distance từ kết quả tìm kiếm của Weaviate và chuyển đổi sang điểm số (Score = 1 - Distance), xếp hạng giảm dần.

## Kết quả Verification

Script `task5_semantic_search.py` với câu lệnh thử nghiệm "hình phạt cho tội tàng trữ ma tuý" đã trả về danh sách các chunks rất phù hợp. Chức năng tìm kiếm cốt lõi của RAG Pipeline đã sẵn sàng.

---

# Hoàn thành Task 6: Lexical Search (Tìm kiếm từ khóa BM25)

Module tìm kiếm từ khóa truyền thống bằng thuật toán BM25 đã được thiết lập thành công.

## Các thay đổi chính

- **Kế thừa Weaviate Built-in BM25**: Thay vì phải tự xây dựng BM25 index bằng Python (`rank-bm25`), chúng ta đã tận dụng sức mạnh có sẵn của Weaviate. Hàm `collection.query.bm25()` tự động tính toán điểm Term Frequency (TF) và Inverse Document Frequency (IDF) ngay trên CSDL Weaviate rất nhanh và chuẩn xác.
- **Kết nối Weaviate**: Tương tự như Task 5, đã trỏ kết nối tìm kiếm tới cổng `8081` (grpc: `50052`).

## Kết quả Verification

Script `task6_lexical_search.py` chạy từ khóa *"Điều 248 tàng trữ trái phép chất ma tuý"* đã tìm ra các đoạn có độ khớp từ khóa (BM25 score) cao nhất. Hiện tại hệ thống đã sở hữu trọn bộ 2 loại tìm kiếm: **Dense Search** (theo nghĩa) và **Lexical Search** (theo từ khóa).

---

# Hoàn thành Task 7: Reranking (Xếp hạng lại)

Module Reranking đã được cập nhật thành công để tương thích hoàn toàn với nền tảng OpenAI, kết hợp sức mạnh của Lexical Search và Semantic Search.

## Các thay đổi chính

- **Cập nhật OpenAI API**: Thay thế toàn bộ mã nguồn sử dụng Gemini sang sử dụng `OpenAI API` (`text-embedding-3-small`) trong các hàm tính toán điểm số (bao gồm cả `rerank_cross_encoder` và `rerank_mmr`).
- **Reciprocal Rank Fusion (RRF)**: Duy trì logic kết hợp thứ hạng từ 2 danh sách kết quả (từ BM25 và từ Cosine Similarity) theo thuật toán RRF để đưa ra kết quả vừa có từ khóa chuẩn, vừa đúng ngữ cảnh.
- **Maximal Marginal Relevance (MMR)**: Hỗ trợ tạo Vector nhúng cho các kết quả trả về bằng OpenAI và tính toán MMR, giúp kết quả hiển thị cho người dùng đa dạng hóa (diverse) hơn, tránh các thông tin bị trùng lặp.

## Kết quả Verification

Hệ thống đã xếp hạng cực kỳ chuẩn xác và hợp lý các kết quả tìm kiếm.

---

# Hoàn thành Task 8: Vectorless RAG (PageIndex)

Giải pháp dự phòng (fallback) sử dụng cơ chế tìm kiếm cấu trúc (structural understanding) của PageIndex.ai đã được tích hợp thành công.

## Các thay đổi chính

- **Tích hợp PageIndex**: Thiết lập biến môi trường `PAGEINDEX_API_KEY` để kết nối với dịch vụ.
- **Upload Tài liệu PDF**: Toàn bộ các tài liệu pháp luật gốc (định dạng `.pdf` trong thư mục `landing/legal`) bao gồm các Thông tư và Nghị định về ma tuý đã được hệ thống tự động quét và đẩy (upload) thành công lên server của PageIndex.ai.
- **Cơ chế Fallback Query**: Hàm `pageindex_search` đã có thể kết nối với server, chờ đợi tài liệu xử lý xong và thực hiện truy vấn mà không cần đến bước Chunking hay Vector Database phức tạp.

## Kết quả Verification

Hệ thống đã nhận diện thành công 3 tệp tin PDF gốc và đẩy lên máy chủ PageIndex. Vectorless RAG đã sẵn sàng để trở thành công cụ cứu cánh (fallback) tuyệt vời.

---

# Hoàn thành Task 9: Retrieval Pipeline (Luồng truy xuất tổng hợp)

Toàn bộ các "mảnh ghép" siêu việt ở trên đã được lắp ráp lại thành một cỗ máy (pipeline) thống nhất.

## Các thay đổi chính

- Các thành phần được cấu hình hoàn chỉnh với `OpenAI API`.
- Pipeline hiện tại hoạt động theo luồng: Truy vấn đồng thời Dense & Sparse -> Ghép điểm bằng RRF (Reciprocal Rank Fusion) -> Xếp hạng (Rerank) -> Nếu điểm quá thấp sẽ tự động chuyển hướng tìm kiếm bằng PageIndex.

## Kết quả Verification

Hệ thống đã chạy thành công qua toàn bộ pipeline để tự động phân luồng và truy xuất kết quả.

---

# Hoàn thành Task 10: Generation (Tạo văn bản RAG với OpenAI)

Mắt xích cuối cùng của quy trình RAG - Đưa thông tin truy xuất được vào LLM để tạo câu trả lời hoàn chỉnh - đã được giải quyết một cách xuất sắc!

## Các thay đổi chính

- **Tinh chỉnh siêu tham số (Hyperparameters)**: 
  - `TOP_K = 5`: Cung cấp đủ thông tin làm bằng chứng nhưng không quá dài để LLM bị xao nhãng.
  - `TEMPERATURE = 0.3`: Phù hợp với RAG pháp luật, yêu cầu tính chính xác cao thay vì sự sáng tạo.
  - `TOP_P = 0.9`: Giúp câu văn mạch lạc và đa dạng từ vựng.
- **Sắp xếp chống trôi (Lost-in-the-middle)**: Hệ thống tự động sắp xếp lại các chunks trước khi đưa vào Prompt (tốt nhất ở đầu, tốt nhì ở cuối) để đảm bảo OpenAI ghi nhớ tối đa thông tin quan trọng.
- **Tích hợp GPT-4o-mini**: Tự động nhận diện và sử dụng OpenAI key để thay thế cho Gemini. 

## Kết quả Verification

Hệ thống đã trả lời các câu hỏi cực kỳ mượt mà bằng tiếng Việt với các bằng chứng (citation) rõ ràng ngay trong câu.

**100% dự án RAG đã hoàn tất thành công!**
