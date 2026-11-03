"""Build assets/broll/catalog.json: thousands of ready-made procedural b-roll presets (topic × template × palette).

usage: python gen_broll_catalog.py [out.json]
Each entry: {id, topic, template, pal, text, sub?, icon?, num?, unit?, items?, seed, tags[]}.
Render any entry: node scripts/broll.mjs render <id> out.mp4 · search: node scripts/broll.mjs search "câu nói".
Add a topic = add one line to TOPICS; templates come from its groups.
"""
import json
import os
import sys
import unicodedata
import zlib

PALS = ["ember", "neon", "ocean", "forest", "gold", "violet", "mono", "sunset", "light", "candy"]

GROUPS = {
    "number": ["bar_chart", "line_chart", "counter_big", "pie", "kpi"],
    "money": ["money_rain", "counter_big", "bar_chart", "kpi", "line_chart"],
    "list": ["checklist", "progress", "timeline_steps"],
    "tech": ["code_rain", "neural", "glitch_text", "browser", "search", "matrix", "orbit_icons"],
    "social": ["likes", "phone_feed", "notifications", "chat"],
    "time": ["clock", "calendar", "countdown", "timeline_steps"],
    "emotion": ["icon_hero", "emoji_burst", "sunburst", "quote_card", "typewriter", "rings"],
    "place": ["globe", "map_pins"],
    "compare": ["versus", "bar_chart"],
    "launch": ["rocket", "countdown", "starfield", "emoji_burst"],
    "news": ["ticker", "glitch_text", "notifications"],
    "music": ["equalizer", "wave_lines", "particles"],
    "idea": ["icon_hero", "rings", "spotlight", "typewriter"],
    "files": ["files", "browser", "checklist"],
    "abstract": ["particles", "blobs", "wave_lines", "hex_grid", "grid_tunnel", "starfield", "sunburst"],
}

# slug | tags (VN, comma) | on-screen text | icon | groups | extras
T = [
    # ---- kinh doanh / bán hàng
    ("doanh-thu", "doanh thu,tăng doanh thu,bán hàng,revenue,thu nhập", "DOANH THU", "💰", "number,money", {"num": 248, "sub": "so với tháng trước"}),
    ("loi-nhuan", "lợi nhuận,lãi,profit,biên lợi nhuận", "LỢI NHUẬN", "📈", "number,money", {"num": 135}),
    ("don-hang", "đơn hàng,chốt đơn,order,khách đặt hàng", "ĐƠN HÀNG MỚI", "🛒", "social,number", {"num": 1250, "items": ["Đơn hàng mới · 1.250.000đ", "Đơn hàng mới · 890.000đ", "Khách vừa thanh toán", "Đơn hàng mới · 2.100.000đ"]}),
    ("khach-hang", "khách hàng,customer,người mua,tệp khách", "KHÁCH HÀNG", "🤝", "number,social", {"num": 3480, "chat": ["Shop ơi còn hàng không ạ?", "Dạ còn ạ, em gửi mẫu nhé 😊", "Chốt 2 cái nha", "Em lên đơn ngay ạ!"]}),
    ("chot-sale", "chốt sale,chốt đơn,closing,tư vấn bán", "CHỐT SALE", "✅", "emotion,number", {"num": 38, "unit": "%"}),
    ("ban-hang-online", "bán hàng online,bán online,shop online,thương mại điện tử,ecommerce", "BÁN ONLINE", "🛍️", "social,number,tech", {}),
    ("livestream", "livestream,live,phát trực tiếp,bán live", "LIVESTREAM", "🔴", "social,number", {"num": 12500}),
    ("khuyen-mai", "khuyến mãi,giảm giá,sale,flash sale,ưu đãi", "GIẢM 50%", "🏷️", "emotion,launch,news", {"num": 50, "unit": "%"}),
    ("gia-ca", "giá,giá cả,chi phí,bảng giá,pricing", "BẢNG GIÁ", "💲", "number,compare", {}),
    ("san-pham", "sản phẩm,product,mặt hàng,ra mắt sản phẩm", "SẢN PHẨM MỚI", "📦", "launch,idea", {}),
    ("thuong-hieu", "thương hiệu,brand,nhận diện,uy tín", "THƯƠNG HIỆU", "⭐", "idea,emotion", {}),
    ("doi-thu", "đối thủ,cạnh tranh,competitor,so sánh", "ĐỐI THỦ", "⚔️", "compare", {"items": ["HỌ", "BẠN"]}),
    ("thi-truong", "thị trường,market,ngành,xu hướng thị trường", "THỊ TRƯỜNG", "🌏", "place,number", {}),
    ("khoi-nghiep", "khởi nghiệp,startup,mở công ty,kinh doanh riêng", "KHỞI NGHIỆP", "🚀", "launch,idea", {}),
    ("doanh-nghiep", "doanh nghiệp,công ty,business,chủ doanh nghiệp", "DOANH NGHIỆP", "🏢", "number,list", {"items": [["Doanh thu", 12, " tỷ"], ["Nhân sự", 85, ""], ["Tăng trưởng", 34, "%"]]}),
    ("chu-shop", "chủ shop,chủ kinh doanh,người bán,tiểu thương", "CHỦ SHOP", "🏪", "social,money", {}),
    ("chuoi-cua-hang", "chuỗi cửa hàng,chi nhánh,mở rộng,nhượng quyền", "MỞ RỘNG CHUỖI", "📍", "place,number", {"items": ["Hà Nội", "Hải Phòng", "Đà Nẵng", "Nha Trang", "TP.HCM"]}),
    ("xuat-khau", "xuất khẩu,quốc tế,toàn cầu,global,nước ngoài", "VƯƠN RA THẾ GIỚI", "🌍", "place", {"items": ["Việt Nam", "Singapore", "Tokyo", "Seoul", "Sydney"]}),
    ("dau-tu", "đầu tư,nhà đầu tư,gọi vốn,investment", "ĐẦU TƯ", "💼", "money,number", {"num": 5, "unit": " tỷ"}),
    ("tai-chinh", "tài chính,quản lý tiền,ngân sách,dòng tiền,cash flow", "DÒNG TIỀN", "💵", "money,number", {}),
    ("tiet-kiem-tien", "tiết kiệm tiền,tiết kiệm chi phí,giảm chi phí,cắt giảm", "TIẾT KIỆM 70%", "🐷", "money,compare", {"num": 70, "unit": "%"}),
    ("luong", "lương,thu nhập,tăng lương,mức lương,salary", "THU NHẬP", "💸", "money,number", {"num": 50, "unit": " triệu"}),
    ("trieu-phu", "triệu phú,giàu,tự do tài chính,thành công tài chính", "TỰ DO TÀI CHÍNH", "🤑", "money,emotion", {"num": 1000000000, "unit": "đ"}),
    ("hop-dong", "hợp đồng,ký kết,đối tác,partnership", "KÝ HỢP ĐỒNG", "✍️", "files,emotion,list", {"items": ["Đàm phán", "Thống nhất điều khoản", "Ký kết", "Triển khai"]}),
    ("bao-cao", "báo cáo,report,số liệu,thống kê,dashboard", "BÁO CÁO", "📊", "number,files", {}),
    ("kpi", "kpi,chỉ số,mục tiêu,okr,đo lường", "KPI", "🎯", "number,list", {"items": [["Doanh thu", 1250, "tr"], ["Khách mới", 340, ""], ["Chuyển đổi", 12, "%"]]}),
    ("quy-trinh", "quy trình,process,các bước,hệ thống,sop", "QUY TRÌNH", "⚙️", "list", {"items": ["Tiếp nhận", "Xử lý", "Kiểm tra", "Bàn giao"]}),
    ("nhan-su", "nhân sự,tuyển dụng,đội ngũ,team,nhân viên", "ĐỘI NGŨ", "👥", "list,social", {"items": ["Tuyển đúng người", "Đào tạo bài bản", "Giao việc rõ", "Thưởng xứng đáng"]}),
    ("lanh-dao", "lãnh đạo,leader,quản lý,ceo,sếp", "LÃNH ĐẠO", "👑", "idea,emotion", {}),
    ("hop", "cuộc họp,meeting,họp hành,thảo luận", "CUỘC HỌP", "🗓️", "time,social", {}),
    # ---- marketing / content
    ("marketing", "marketing,tiếp thị,quảng bá,chiến dịch", "MARKETING", "📣", "number,social,list", {"items": ["Nghiên cứu", "Nội dung", "Phân phối", "Đo lường"], "num": 180}),
    ("quang-cao", "quảng cáo,chạy ads,facebook ads,tiktok ads,ads", "QUẢNG CÁO", "📢", "number,money", {"num": 320, "sub": "ROAS tăng"}),
    ("viral", "viral,lan truyền,triệu view,nổi tiếng,trend", "VIRAL", "🔥", "social,number,launch", {"num": 2400000}),
    ("luot-xem", "lượt xem,view,views,người xem", "TRIỆU VIEW", "👀", "number,social", {"num": 1200000}),
    ("follower", "follower,người theo dõi,fan,subscriber,tăng follow", "FOLLOWERS", "👥", "social,number", {"num": 100000}),
    ("tuong-tac", "tương tác,like,thả tim,engagement,bình luận", "TƯƠNG TÁC", "❤️", "social", {"num": 128000}),
    ("binh-luan", "bình luận,comment,phản hồi,inbox,tin nhắn", "BÌNH LUẬN", "💬", "social", {"chat": ["Hay quá ạ!", "Cảm ơn bạn nha ❤️", "Xin link với ạ", "Gửi bạn rồi nhé!"]}),
    ("content", "content,nội dung,sáng tạo nội dung,creator,làm nội dung", "CONTENT", "✍️", "idea,list,social", {"items": ["Ý tưởng", "Kịch bản", "Quay", "Dựng", "Đăng"]}),
    ("kich-ban", "kịch bản,script,viết kịch bản,ý tưởng video", "KỊCH BẢN", "📝", "files,idea,list", {}),
    ("thumbnail", "thumbnail,ảnh bìa,tiêu đề,hook", "HOOK 3 GIÂY", "🎣", "idea,emotion", {}),
    ("tiktok", "tiktok,video ngắn,short,reels", "VIDEO NGẮN", "🎵", "social,music", {"items": ["Video lên xu hướng 🔥", "+12.000 follow mới", "Bình luận: xin link ạ", "Đã chia sẻ 3.400 lần"]}),
    ("youtube", "youtube,kênh youtube,vlog,video dài", "YOUTUBE", "▶️", "social,number", {"num": 500000}),
    ("facebook", "facebook,fanpage,trang,group", "FANPAGE", "👍", "social,number", {}),
    ("seo", "seo,google,tìm kiếm,top google,từ khoá", "TOP GOOGLE", "🔍", "tech,number", {"text_search": "cách tăng doanh thu online"}),
    ("email", "email,email marketing,bản tin,newsletter", "EMAIL", "📧", "social,files", {}),
    ("khach-hang-tiem-nang", "khách hàng tiềm năng,lead,data khách,phễu", "LEAD", "🧲", "number,list", {"items": ["Tiếp cận", "Quan tâm", "Cân nhắc", "Mua hàng"]}),
    ("pheu-ban-hang", "phễu bán hàng,funnel,chuyển đổi,conversion", "PHỄU BÁN HÀNG", "🔻", "list,number", {"items": ["Nhận biết", "Quan tâm", "Mong muốn", "Hành động"]}),
    ("kol", "kol,koc,influencer,người nổi tiếng,review", "KOL REVIEW", "🌟", "social,emotion", {}),
    ("ca-nhan", "thương hiệu cá nhân,personal brand,xây kênh", "THƯƠNG HIỆU CÁ NHÂN", "🪞", "idea,social", {}),
    # ---- AI / công nghệ
    ("ai", "ai,trí tuệ nhân tạo,artificial intelligence,máy học", "AI", "🤖", "tech,idea", {}),
    ("chatgpt", "chatgpt,claude,chatbot,gpt,trợ lý ai", "TRỢ LÝ AI", "💬", "tech,social", {"chat": ["Viết giúp mình kịch bản video", "Đây là kịch bản 60 giây cho bạn ✨", "Thêm hook mạnh hơn", "Đã cập nhật!"]}),
    ("tu-dong-hoa", "tự động hoá,automation,tự động,workflow,không cần làm tay", "TỰ ĐỘNG 100%", "⚙️", "tech,list", {"items": ["Nhận yêu cầu", "AI xử lý", "Kiểm tra", "Xuất bản"]}),
    ("prompt", "prompt,ra lệnh,câu lệnh,gõ lệnh", "CHỈ CẦN RA LỆNH", "⌨️", "tech", {"text_search": "edit video này giống mẫu"}),
    ("lap-trinh", "lập trình,code,developer,phần mềm,coding", "LẬP TRÌNH", "👨‍💻", "tech", {}),
    ("website", "website,trang web,landing page,web", "WEBSITE", "🌐", "tech,files", {}),
    ("app", "ứng dụng,app,mobile app,điện thoại", "ỨNG DỤNG", "📱", "tech,social", {}),
    ("du-lieu", "dữ liệu,data,big data,phân tích dữ liệu", "DỮ LIỆU", "🧮", "tech,number", {}),
    ("bao-mat", "bảo mật,an toàn,hacker,security,lừa đảo", "BẢO MẬT", "🔒", "tech,news", {}),
    ("cloud", "cloud,đám mây,lưu trữ,server", "CLOUD", "☁️", "tech,files", {}),
    ("robot", "robot,máy móc,nhà máy thông minh", "ROBOT", "🦾", "tech,launch", {}),
    ("cong-nghe-moi", "công nghệ mới,đột phá,tương lai,innovation", "TƯƠNG LAI", "🔮", "tech,launch,idea", {}),
    ("chuyen-doi-so", "chuyển đổi số,số hoá,digital", "CHUYỂN ĐỔI SỐ", "💡", "tech,list", {}),
    ("ai-video", "ai edit video,dựng video bằng ai,video ai,edit tự động", "AI EDIT VIDEO", "🎬", "tech,list,launch", {"items": ["Cắt khoảng lặng", "Phụ đề tự động", "Chèn nhạc nền", "Hiệu ứng chuyển cảnh", "Xuất video"], "chat": ["Anh ơi video này edit bằng gì vậy?", "Bằng AI 100% luôn em 😎", "Thật á? Mất bao lâu ạ?", "Có 10 phút thôi!"]}),
    ("ai-anh", "ai tạo ảnh,thiết kế ai,midjourney,tạo hình", "AI TẠO ẢNH", "🎨", "tech,idea", {}),
    ("ai-giong-noi", "giọng nói ai,lồng tiếng,voice,text to speech", "GIỌNG NÓI AI", "🎙️", "tech,music", {}),
    # ---- video / sản xuất
    ("edit-video", "edit video,dựng video,hậu kỳ,cắt ghép,premiere,capcut", "EDIT VIDEO", "🎞️", "list,tech", {"items": ["Cắt", "Phụ đề", "Nhạc", "Hiệu ứng", "Xuất"]}),
    ("quay-phim", "quay phim,quay video,camera,máy quay", "QUAY VIDEO", "🎥", "list,idea", {}),
    ("phu-de", "phụ đề,sub,caption,chữ chạy", "PHỤ ĐỀ TỰ ĐỘNG", "💬", "tech,list", {}),
    ("am-nhac", "âm nhạc,nhạc nền,bài hát,giai điệu,music", "NHẠC NỀN", "🎶", "music", {}),
    ("hieu-ung", "hiệu ứng,effect,chuyển cảnh,motion", "HIỆU ỨNG", "✨", "emotion,abstract", {}),
    ("podcast", "podcast,talkshow,trò chuyện,phỏng vấn", "PODCAST", "🎧", "music,social", {}),
    # ---- thời gian / năng suất
    ("thoi-gian", "thời gian,mất thời gian,tốn thời gian,hàng giờ", "THỜI GIAN", "⏰", "time", {"num": 8}),
    ("deadline", "deadline,hạn chót,gấp,áp lực", "DEADLINE", "⏳", "time,news", {}),
    ("tiet-kiem-thoi-gian", "tiết kiệm thời gian,nhanh hơn,chỉ còn vài phút,tốc độ", "NHANH GẤP 10 LẦN", "⚡", "time,compare,launch", {"items": ["4 TIẾNG", "10 PHÚT"]}),
    ("nang-suat", "năng suất,hiệu suất,làm việc hiệu quả,productivity", "NĂNG SUẤT x3", "🚀", "number,list", {"num": 300, "unit": "%"}),
    ("ke-hoach", "kế hoạch,lịch trình,lên kế hoạch,plan,lộ trình", "KẾ HOẠCH", "🗓️", "time,list", {"items": ["Mục tiêu", "Chia nhỏ", "Lịch tuần", "Review"]}),
    ("thoi-quen", "thói quen,mỗi ngày,kỷ luật,habit,routine", "MỖI NGÀY", "📅", "time,list", {"items": ["Dậy sớm", "Đọc sách", "Tập thể dục", "Lên kế hoạch"]}),
    ("30-ngay", "30 ngày,thử thách,challenge,1 tháng", "THỬ THÁCH 30 NGÀY", "🔥", "time,launch", {"num": 1}),
    ("lam-viec", "làm việc,công việc,văn phòng,work", "CÔNG VIỆC", "💼", "list,files", {}),
    ("tap-trung", "tập trung,focus,sâu,không xao nhãng", "TẬP TRUNG", "🎯", "idea,abstract", {}),
    # ---- giáo dục / kiến thức
    ("hoc-tap", "học tập,học,kiến thức,khoá học,course", "HỌC TẬP", "📚", "list,idea", {"items": ["Học", "Thực hành", "Sai", "Sửa", "Thành thạo"]}),
    ("khoa-hoc", "khoá học,đào tạo,lớp học,training,học viên", "KHOÁ HỌC", "🎓", "list,number", {"num": 5000, "sub": "học viên"}),
    ("bi-quyet", "bí quyết,mẹo,tips,cách làm,hướng dẫn", "BÍ QUYẾT", "💡", "idea,list", {"items": ["Bước 1: Chuẩn bị", "Bước 2: Làm thử", "Bước 3: Tối ưu", "Bước 4: Nhân bản"]}),
    ("sai-lam", "sai lầm,lỗi,sai,thất bại,đừng làm", "SAI LẦM", "❌", "emotion,compare", {"items": ["SAI", "ĐÚNG"]}),
    ("bi-mat", "bí mật,ít ai biết,sự thật,hé lộ", "SỰ THẬT", "🤫", "idea,news", {}),
    ("cau-hoi", "câu hỏi,hoài nghi,liệu,có thật không,tại sao", "LIỆU CÓ THẬT?", "❓", "idea,emotion", {"chat": ["Cái này có thật không vậy?", "Thật 100%, xem nè 👇", "Wow, phải thử ngay!", "Làm theo video nhé"]}),
    ("tri-thuc", "sách,đọc sách,tri thức,trí tuệ", "ĐỌC SÁCH", "📖", "idea,list", {}),
    ("ngoai-ngu", "tiếng anh,ngoại ngữ,english,học tiếng", "TIẾNG ANH", "🗣️", "list,social", {}),
    ("tre-em", "trẻ em,con cái,bé,giáo dục con", "TRẺ EM", "🧒", "emotion,list", {}),
    # ---- sức khoẻ / đời sống
    ("suc-khoe", "sức khoẻ,khoẻ mạnh,health,miễn dịch", "SỨC KHOẺ", "💪", "list,number", {"items": ["Ngủ đủ 8 tiếng", "Uống đủ nước", "Vận động 30 phút", "Ăn nhiều rau"]}),
    ("gym", "gym,tập luyện,thể hình,giảm cân,cơ bắp", "TẬP GYM", "🏋️", "number,list,time", {"num": 12, "unit": "kg"}),
    ("an-uong", "ăn uống,dinh dưỡng,thực phẩm,eat clean", "DINH DƯỠNG", "🥗", "list,number", {"items": ["Đạm", "Tinh bột tốt", "Chất béo tốt", "Rau xanh"]}),
    ("giac-ngu", "giấc ngủ,ngủ,mất ngủ,nghỉ ngơi", "GIẤC NGỦ", "😴", "time,emotion", {}),
    ("thien", "thiền,bình an,chữa lành,mindfulness", "BÌNH AN", "🧘", "emotion,abstract", {}),
    ("lam-dep", "làm đẹp,mỹ phẩm,skincare,da đẹp,spa", "DA ĐẸP", "✨", "emotion,compare", {"items": ["TRƯỚC", "SAU"]}),
    ("thoi-trang", "thời trang,quần áo,phong cách,outfit", "PHONG CÁCH", "👗", "emotion,social", {}),
    ("am-thuc", "ẩm thực,món ăn,nhà hàng,quán ăn,nấu ăn", "ẨM THỰC", "🍜", "emotion,social", {}),
    ("ca-phe", "cà phê,coffee,quán cà phê", "CÀ PHÊ", "☕", "emotion,abstract", {}),
    ("du-lich", "du lịch,travel,khám phá,chuyến đi", "DU LỊCH", "✈️", "place,launch", {"items": ["Hà Giang", "Hội An", "Đà Lạt", "Phú Quốc", "Bangkok"]}),
    ("gia-dinh", "gia đình,bố mẹ,vợ chồng,người thân", "GIA ĐÌNH", "👨‍👩‍👧", "emotion", {}),
    ("tinh-yeu", "tình yêu,yêu,người yêu,hẹn hò", "TÌNH YÊU", "💕", "emotion,social", {}),
    ("nha-dat", "bất động sản,nhà đất,căn hộ,mua nhà", "BẤT ĐỘNG SẢN", "🏠", "number,place,money", {}),
    ("o-to", "ô tô,xe hơi,xe,car", "Ô TÔ", "🚗", "launch,number", {}),
    ("the-thao", "thể thao,bóng đá,chạy bộ,marathon", "THỂ THAO", "⚽", "launch,emotion", {}),
    ("game", "game,chơi game,esports,gaming", "GAMING", "🎮", "tech,launch", {}),
    ("pet", "thú cưng,chó,mèo,pet", "THÚ CƯNG", "🐶", "emotion,social", {}),
    ("moi-truong", "môi trường,xanh,thiên nhiên,bền vững", "SỐNG XANH", "🌱", "emotion,place", {}),
    ("tet", "tết,năm mới,lì xì,xuân", "TẾT", "🧧", "emotion,launch,time", {}),
    ("su-kien", "sự kiện,event,hội thảo,workshop", "SỰ KIỆN", "🎤", "time,launch,social", {}),
    ("le-hoi", "lễ hội,tiệc,party,ăn mừng,chúc mừng", "ĂN MỪNG", "🎉", "emotion,launch", {}),
    # ---- cảm xúc / động lực / tư duy
    ("thanh-cong", "thành công,chiến thắng,đạt được,kết quả", "THÀNH CÔNG", "🏆", "emotion,number,launch", {}),
    ("that-bai", "thất bại,vấp ngã,khó khăn,đau khổ", "THẤT BẠI", "💔", "emotion,compare", {}),
    ("dong-luc", "động lực,cảm hứng,truyền cảm hứng,motivation", "ĐỪNG BỎ CUỘC", "🔥", "emotion,idea", {}),
    ("noi-so", "nỗi sợ,sợ hãi,lo lắng,áp lực", "NỖI SỢ", "😨", "emotion,news", {}),
    ("vui-ve", "vui,hạnh phúc,vui vẻ,happy,cười", "VUI!", "😄", "emotion,music", {}),
    ("buon", "buồn,cô đơn,tâm trạng,nhớ", "buồn…", "🥀", "emotion,abstract", {}),
    ("bat-ngo", "bất ngờ,wow,không thể tin,sốc", "WOW!", "🤯", "emotion,news,launch", {}),
    ("tu-duy", "tư duy,mindset,suy nghĩ,góc nhìn", "TƯ DUY", "🧠", "idea,tech", {}),
    ("y-tuong", "ý tưởng,sáng tạo,idea,nảy ra", "Ý TƯỞNG", "💡", "idea", {}),
    ("muc-tieu", "mục tiêu,đích đến,tầm nhìn,goal", "MỤC TIÊU", "🎯", "idea,number,list", {"items": ["Cụ thể", "Đo được", "Khả thi", "Có hạn chót"]}),
    ("lua-chon", "lựa chọn,quyết định,cân nhắc,phân vân", "LỰA CHỌN", "🤔", "compare,idea", {"items": ["CÁCH CŨ", "CÁCH MỚI"]}),
    ("truoc-sau", "trước và sau,trước sau,thay đổi,biến đổi,transformation", "TRƯỚC / SAU", "🔁", "compare", {"items": ["TRƯỚC", "SAU"]}),
    ("bang-chung", "bằng chứng,chứng minh,kết quả thật,feedback,review", "KẾT QUẢ THẬT", "📸", "social,number", {"items": ["Đã nhận hàng, rất ưng ❤️", "Shop tư vấn nhiệt tình", "Sẽ ủng hộ tiếp ạ", "5 sao!"], "chat": ["Nhận hàng rồi, đẹp quá!", "Cảm ơn chị đã tin tưởng ❤️", "Lần sau mua tiếp nha", "Dạ shop luôn sẵn sàng ạ"]}),
    ("cam-on", "cảm ơn,biết ơn,tri ân", "CẢM ƠN", "🙏", "emotion", {}),
    ("dang-ky", "đăng ký,subscribe,theo dõi kênh,follow", "ĐĂNG KÝ NGAY", "🔔", "social,launch", {}),
    ("link", "link,bio,inbox,liên hệ,nhắn tin", "LINK Ở BIO", "👇", "social,emotion", {}),
    ("canh-bao", "cảnh báo,chú ý,lưu ý,warning,nguy hiểm", "CẢNH BÁO", "⚠️", "news,emotion", {}),
    ("tin-tuc", "tin tức,tin nóng,mới nhất,breaking,cập nhật", "TIN NÓNG", "📰", "news", {"items": ["TIN NÓNG", "MỚI NHẤT", "CẬP NHẬT", "ĐỘC QUYỀN"]}),
    ("top", "top,xếp hạng,số 1,hàng đầu,tốt nhất", "TOP 1", "🥇", "number,emotion", {}),
    ("mien-phi", "miễn phí,free,tặng,quà tặng", "MIỄN PHÍ", "🎁", "emotion,launch", {}),
    ("100-phan-tram", "100%,hoàn toàn,tuyệt đối,trọn vẹn", "100%", "💯", "number,emotion", {"num": 100, "unit": "%"}),
    ("de-dang", "dễ dàng,đơn giản,ai cũng làm được,chỉ cần", "SIÊU ĐƠN GIẢN", "👌", "list,emotion", {"items": ["Mở máy", "Ra lệnh", "Nhận kết quả"]}),
    ("cong-dong", "cộng đồng,group,thành viên,hội nhóm", "CỘNG ĐỒNG", "🫂", "social,number,place", {"num": 50000}),
    ("ket-noi", "kết nối,mạng lưới,network,quan hệ", "KẾT NỐI", "🔗", "tech,place", {}),
    ("phat-trien", "phát triển,tăng trưởng,growth,bứt phá,scale", "BỨT PHÁ", "📈", "number,launch", {"num": 500}),
    ("hanh-trinh", "hành trình,câu chuyện,quá trình,từ con số 0", "HÀNH TRÌNH", "🧭", "time,list,place", {"items": ["Con số 0", "Thử sai", "Bước ngoặt", "Thành công"]}),
    ("nhieu", "rất nhiều,vô số,đa dạng,sinh động,phong phú", "VÔ SỐ", "🌈", "abstract,emotion", {}),
    ("dem-nguoc", "đếm ngược,sắp ra mắt,chuẩn bị,sẵn sàng", "SẴN SÀNG?", "⏱️", "launch,time", {}),
    ("ket-luan", "kết luận,tóm lại,cuối cùng,chốt lại", "TÓM LẠI", "📌", "list,idea", {"items": ["Hiểu vấn đề", "Chọn công cụ", "Làm ngay hôm nay"]}),
]

ABSTRACT_SEEDS = 6

# Which templates can use a topic's "items", and in what shape.
_texts = lambda it: all(isinstance(x, str) for x in it)
ITEMS_OK = {tp: (lambda it: False) for g in GROUPS.values() for tp in g}
ITEMS_OK.update({tp: _texts for tp in ("checklist", "progress", "timeline_steps", "notifications", "ticker", "map_pins")})
ITEMS_OK["versus"] = lambda it: _texts(it) and len(it) == 2
ITEMS_OK["kpi"] = lambda it: isinstance(it[0], list)
NEEDS_ITEMS = {"checklist", "progress", "timeline_steps", "notifications", "map_pins", "kpi", "ticker"}


def slug(s):
    s = unicodedata.normalize("NFD", s.lower()).replace("đ", "d")
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return "".join(ch if ch.isalnum() else "-" for ch in s).strip("-")


def pick_pals(key, k):
    start = zlib.crc32(key.encode()) % len(PALS)
    pals = ["ember"] + [PALS[(start + i * 3) % len(PALS)] for i in range(len(PALS))]
    out = []
    for p in pals:
        if p not in out:
            out.append(p)
    return out[:k]


def build():
    out = []
    for sl, tags, text, icon, groups, ex in T:
        tpls = []
        for g in groups.split(","):
            for tp in GROUPS[g]:
                if tp not in tpls:
                    tpls.append(tp)
        tags_l = [t.strip() for t in tags.split(",")]
        # Content-bearing templates only when the topic supplies its own items (their defaults are about video editing).
        tpls = [tp for tp in tpls if (tp not in NEEDS_ITEMS or ("items" in ex and ITEMS_OK[tp](ex["items"]))) and (tp != "chat" or "chat" in ex)]
        tpls = tpls or GROUPS["emotion"][:3]
        if "chat" in ex:
            tpls = ["chat"] + [tp for tp in tpls if tp != "chat"]  # a written conversation is the strongest visual for these topics
        for tp in tpls[:9]:
            for pal in pick_pals(sl + tp, 4):
                e = {"id": f"{sl}--{tp}--{pal}", "topic": sl, "template": tp, "pal": pal, "text": text, "icon": icon,
                     "seed": zlib.crc32((sl + tp).encode()) % 97 + 1, "tags": tags_l + [tp]}
                for k in ("num", "unit", "sub", "items"):
                    if k in ex:
                        e[k] = ex[k]
                if tp == "search":
                    e["text"] = ex.get("text_search", tags_l[0])
                if tp == "pie" and not (0 < e.get("num", 78) <= 100 and e.get("unit", "%") == "%"):
                    e.pop("num", None)
                    e.pop("unit", None)
                if e.get("num", 0) >= 1000 and "unit" not in e:
                    e["unit"] = ""  # counts, not percentages
                if tp == "counter_big" and "num" not in ex:
                    e["num"] = 1000
                if tp == "versus" and "items" not in ex:
                    e["items"] = ["TRƯỚC", "SAU"]
                if tp == "chat":
                    e["items"] = ex["chat"]
                elif "items" in e and not ITEMS_OK[tp](e["items"]):
                    e.pop("items")  # template falls back to its own defaults
                if tp in ("typewriter", "quote_card", "glitch_text", "ticker", "icon_hero", "spotlight"):
                    e["sub"] = e.get("sub") or tags_l[0]
                out.append(e)
    for tp in GROUPS["abstract"]:
        for pal in PALS:
            for sd in range(1, ABSTRACT_SEEDS + 1):
                out.append({"id": f"bg--{tp}--{pal}--{sd}", "topic": "background", "template": tp, "pal": pal, "seed": sd,
                            "tags": ["nền", "background", "trừu tượng", "abstract", tp, pal]})
    return out


if __name__ == "__main__":
    dst = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "assets", "broll", "catalog.json")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    cat = build()
    ids = [e["id"] for e in cat]
    assert len(ids) == len(set(ids)), "duplicate ids"
    json.dump(cat, open(dst, "w"), ensure_ascii=False, separators=(",", ":"))
    from collections import Counter
    print(f"{len(cat)} b-roll presets · {len(T)} topics · {len(set(e['template'] for e in cat))} templates -> {dst}")
    print(Counter(e["template"] for e in cat).most_common(6))
