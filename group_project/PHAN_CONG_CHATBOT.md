# Khung Y Tuong + Phan Cong Chi Tiet (RAG Chatbot)

## 1) Muc tieu nhom

- Xay dung chatbot hoi dap ve phap luat ma tuy va tin tuc lien quan.
- Cau tra loi co citation, co hoi dap tiep noi (follow-up), va hien thi nguon trich dan.
- Co bo evaluation doc lap de do chat luong pipeline theo dung yeu cau 2.

## 2) Khung y tuong san pham

### Luong xu ly tong quan

1. Thu thap va chuan hoa du lieu (legal + news).
2. Tao chunks, indexing va retrieval (semantic + lexical + rerank + page index).
3. Pipeline tra loi: retrieve -> rerank -> generate + citation.
4. Frontend chat de nguoi dung hoi dap, xem citation va lich su hoi dap.
5. Evaluation pipeline de do faithfulness, relevance, recall, precision va so sanh A/B.

### Huong chia giai doan

- Giai doan 1 (Nen tang): du lieu + pipeline retrieval hoat dong.
- Giai doan 2 (San pham): chatbot UI va luong hoi dap dau-cuoi.
- Giai doan 3 (Chat luong): evaluation + bao cao ket qua + tai lieu demo.

## 3) Phan cong chi tiet theo thanh vien

## 3.1 Thai Minh - Thu thap tai lieu, lam data

### Nhiem vu chinh

- Thu thap van ban phap ly va tin tuc lien quan den ma tuy.
- Lam sach du lieu dau vao, loai bo noi dung trung lap, dung format.
- Chuan hoa markdown/text de dua vao pipeline chunking.

### Dau ra can ban giao

- Thu muc du lieu day du trong data/landing va data/standardized.
- Danh sach nguon va quy tac loc du lieu.
- Mau file dau vao da duoc chuan hoa de team index truc tiep.

## 3.2 Anh - Lam chatbot

### Nhiem vu chinh

- Noi retrieval pipeline voi generation de tra loi co citation.
- Ho tro conversation memory cho follow-up questions.
- Dong bo API/ham de frontend goi va hien thi source documents.

### Dau ra can ban giao

- Luong hoi dap chatbot chay duoc end-to-end.
- Ham tra ve ket qua dang: answer + sources + metadata can thiet.
- Ban chat demo de team test nhanh truoc khi tich hop frontend.

## 3.3 Tam - Docs huong dan dung app, tai lieu demo

### Nhiem vu chinh

- Viet huong dan cai dat va chay app cho giang vien/nguoi demo.
- Viet kich ban demo ngan gon: input mau, output mong doi, diem nhan.
- Tong hop mo ta kien truc va cach su dung cac module.

### Dau ra can ban giao

- Tai lieu huong dan su dung app trong README/tai lieu bo sung.
- Tai lieu demo buoi bao cao (cac buoc + cau hoi mau + expected behavior).

## 3.4 Em - Danh gia chat luong chatbot (tham chieu yeu cau 2)

### Nhiem vu chinh

- Tao golden dataset toi thieu 15 cap Q&A (question, expected_answer, expected_context).
- Trien khai evaluation pipeline theo 1 framework (uu tien RAGAS hoac DeepEval).
- Do 4 metric bat buoc:
  - Faithfulness
  - Answer Relevance
  - Context Recall
  - Context Precision
- Chay so sanh A/B it nhat 2 cau hinh:
  - Vi du: co reranking vs khong reranking
  - Hoac hybrid retrieval vs dense-only
- Phan tich mau loi (worst performers) va de xuat cai tien.

### Dau ra can ban giao

- group_project/evaluation/golden_dataset.json
- group_project/evaluation/eval_pipeline.py
- group_project/evaluation/results.md

## 3.5 Quang Minh - Frontend

### Nhiem vu chinh

- Xay dung giao dien chat (Streamlit/Gradio/Chainlit).
- Hien thi lich su hoi dap, citation va danh sach source documents.
- Toi uu trai nghiem demo: de nhap cau hoi, de xem nguon, de thu follow-up.

### Dau ra can ban giao

- Frontend chat tich hop chatbot backend.
- Giao dien chay on dinh tren local de demo trong lop.

## 4) Checklist phoi hop giua cac vai tro

- Thai Minh ban giao data standardized truoc khi index chot.
- Anh va Quang Minh thong nhat contract du lieu cho cau tra loi + citation.
- Em chot format output cua pipeline de eval script doc duoc thong nhat.
- Tam chot tai lieu huong dan sau khi frontend va eval dat muc toi thieu de demo.

## 5) Dinh nghia hoan thanh

- Chatbot tra loi duoc cau hoi, co citation va follow-up memory.
- Frontend su dung duoc trong demo thuc te.
- Evaluation co diem so, co so sanh A/B, co nhan xet cai tien.
- Co tai lieu huong dan dung app va kich ban demo ro rang.